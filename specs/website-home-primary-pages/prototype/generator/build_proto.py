#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fenixd 官网原型生成器（仿样级 plain-html · 视觉参照、无约束力）
产出 5 张自包含单文件 HTML：index / why / capabilities / docs / community
- 设计候选来源：ui-ux-pro-max --design-system（Dark OLED slate + 开发者 mono 排版 +
  FAQ/Documentation Landing 版式），经两遍式流程修订（去 glow / 去紫渐变 / SVG 图标 /
  绿色只留「已验证」语义、蓝只留链接）
- 主题缺画像依据说明：工程无既有主题 token，取 ui-ux-pro-max 候选 + 两遍式修订
- 单源 CSS / 导航 / 页脚 / i18n 引擎，保证跨页一致；i18n 内联字典中英切换
"""
import json, os, re, shutil

# ---- Round-13: docs 页引用真实 help 文档（/root/fenixd/docs/help/*.md） ----
HELP_SRC = "/root/fenixd/docs/help"
FMAP = {
    "01": "01-quick-start.md", "02": "02-concepts.md", "03": "03-lifecycle.md",
    "04": "04-cli.md", "05": "05-verification.md", "06": "06-governance.md",
    "07": "07-safeguards.md", "08": "08-dashboard.md", "09": "09-config.md",
    "10": "10-artifacts.md", "11": "11-logs.md", "12": "12-faq.md",
    "13": "13-self-update.md", "14": "14-knowledge-atlas.md",
    "15": "15-dsh-harness-runbook.md", "00": "README.md",
}

def help_meta(no, fname):
    """读取 help md，返回 (真实标题, 摘要)"""
    lines = open(f"{HELP_SRC}/{fname}", encoding="utf-8").read().splitlines()
    title = ""
    for ln in lines[:8]:
        m = re.match(r"^#\s+(.+)$", ln.strip())
        if m:
            title = m.group(1).strip()
            break
    digest = ""
    for ln in lines[1:80]:
        t = ln.strip()
        if not t or t.startswith(("#", "|", ">", "```", "- ", "*", "!")):
            continue
        t = re.sub(r"[#*`\[\]]", "", t)
        t = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) < 10:
            continue
        digest = (t[:66] + "…") if len(t) > 66 else t
        break
    return title, digest
_MD_CSS = ("body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:#1f2937;"
 "max-width:860px;margin:0 auto;padding:48px 24px;line-height:1.75;font-size:15px}"
 "h1{font-size:30px;border-bottom:2px solid #e5e7eb;padding-bottom:12px}"
 "h2{font-size:22px;margin-top:36px}h3{font-size:17px;margin-top:28px}"
 "code{background:#f3f4f6;border:1px solid #e5e7eb;border-radius:4px;padding:1px 5px;font-size:13px;"
 "font-family:ui-monospace,Menlo,Consolas,monospace}"
 "pre{background:#0f172a;color:#e2e8f0;padding:14px 16px;border-radius:10px;overflow-x:auto}"
 "pre code{background:none;border:0;color:inherit;padding:0}"
 "table{border-collapse:collapse;margin:16px 0;width:100%}th,td{border:1px solid #e5e7eb;padding:7px 11px;"
 "font-size:13.5px;text-align:left}th{background:#f9fafb}tr:nth-child(even) td{background:#fafafa}"
 "blockquote{border-left:3px solid #d1d5db;margin:14px 0;padding:4px 16px;color:#6b7280;background:#f9fafb}"
 "hr{border:0;border-top:1px solid #e5e7eb;margin:28px 0}a{color:#9c2f81}"
 ".back{display:inline-block;margin-bottom:20px;font-size:13.5px;color:#9c2f81;text-decoration:none}"
 ".back:hover{text-decoration:underline}.meta{color:#9ca3af;font-size:12px;margin-top:40px;"
 "border-top:1px solid #e5e7eb;padding-top:12px}")
_MD_CSS += ("pre.mermaid{background:none;border:0;padding:0;margin:16px 0;overflow-x:auto;text-align:center}"
 "pre.mermaid svg{max-width:100%;height:auto}"
 ".mm-err{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;color:#4b5563;"
 "white-space:pre-wrap;text-align:left}")

def _md_inline(t):
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    def _link(m):
        href = m.group(2)
        if href.endswith(".md"):
            href = href[:-3] + ".html"
        return f'<a href="{href}">{m.group(1)}</a>'
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, t)
    return t

def md_to_html(src, fname):
    """轻量 markdown→自包含 HTML（标题/段落/fenced 代码/表格/列表/引用/hr/行内样式）"""
    out, i, lines = [], 0, open(src, encoding="utf-8").read().splitlines()
    while i < len(lines):
        t = lines[i].rstrip()
        if not t.strip():
            i += 1
            continue
        if t.startswith("```"):
            lang = t[3:].strip().lower()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            esc = (lambda x: x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            if lang == "mermaid":
                # 真图形渲染：保留原文，页尾 vendor mermaid.js 消费（同 dashboard help 页管线）
                out.append('<pre class="mermaid">' + esc("\n".join(buf)) + "</pre>")
            else:
                out.append("<pre><code>" + esc("\n".join(buf)) + "</code></pre>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", t)
        if m:
            lv = len(m.group(1))
            out.append(f"<h{lv}>{_md_inline(m.group(2))}</h{lv}>")
            i += 1
            continue
        if re.match(r"^(---|\*\*\*)\s*$", t):
            out.append("<hr>")
            i += 1
            continue
        if t.lstrip().startswith("|"):
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.match(r"^:?-+:?$", c) for c in row):
                    buf.append(row)
                i += 1
            if buf:
                head = "".join(f"<th>{_md_inline(c)}</th>" for c in buf[0])
                body = "".join("<tr>" + "".join(f"<td>{_md_inline(c)}</td>" for c in r) + "</tr>" for r in buf[1:])
                out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", t):
            items, ol = [], bool(re.match(r"^\s*\d+\.", t))
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]).strip())
                i += 1
            tag = "ol" if ol else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_md_inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if t.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + _md_inline(" ".join(buf)) + "</blockquote>")
            continue
        buf = [t]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|```|\||\s*([-*]|\d+\.)\s|>|---)", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>" + _md_inline(" ".join(buf)) + "</p>")
    title = re.search(r"<h1>(.*?)</h1>", "".join(out))
    t = title.group(1) if title else fname
    return (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{t} · Fenixd 帮助</title>'
            f"<style>{_MD_CSS}</style></head><body>"
            f'<a class="back" href="../docs.html">← 返回文档中心</a>'
            + "".join(out) +
            f'<p class="meta">本页由 Fenixd 仓库 docs/help/{fname} 渲染生成。</p>'
            + ('<script src="../mermaid.min.js"></script><script>'
               'mermaid.initialize({startOnLoad:false,theme:"neutral",securityLevel:"strict",'
               'fontFamily:"system-ui,-apple-system,sans-serif",' 
               'fontSize:14,themeVariables:{fontSize:"14px"},'
               'sequence:{actorFontSize:14,messageFontSize:14,noteFontSize:14}});'
               'mermaid.run({querySelector:"pre.mermaid"}).catch(function(e){'
               'document.querySelectorAll("pre.mermaid").forEach(function(p){'
               'if(!p.querySelector("svg")){p.classList.add("mm-err");}});});'
               "</script>") if 'class="mermaid"' in "".join(out) else ''
            + "</body></html>")


OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 生成器位于 prototype/generator/，产物落原型根

# ============================================================ ICONS（内联 SVG，禁 emoji）
def icon(name, cls="ic"):
    P = {
        "lu-file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
        "lu-shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
        "lu-list-checks": '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
        "lu-git-branch": '<line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
        "lu-badge-check": '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"/><path d="m9 12 2 2 4-4"/>',
        "lu-scale": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
        "lu-calendar-clock": '<path d="M21 7.5V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h3.5"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h5"/><path d="M17.5 17.5 16 16.3V14"/><circle cx="16" cy="16" r="6"/>',
        "lu-git-merge": '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>',
        "lu-heart-pulse": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"/>',
        "lu-server": '<rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/>',
        "lu-layout-dashboard": '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
        "lu-scroll-text": '<path d="M15 12h-5"/><path d="M15 8h-5"/><path d="M19 17V5a2 2 0 0 0-2-2H4"/><path d="M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v1a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v2a1 1 0 0 0 1 1h3"/>',
        "lu-square-terminal": '<path d="m7 11 2-2-2-2"/><path d="M11 13h4"/><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>',
        "flame": '<path d="M12 3c1.5 3-1.5 4.5-1.5 7A3.5 3.5 0 0 0 14 13.4c1.8-.6 3-2.4 3-4.4 2 2 3 4.5 3 6.9A8 8 0 1 1 5 15.5C5 10.5 9 8.5 9 5c0-.7-.3-1.4 3-2z"/>',
        "spec": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
        "loop": '<path d="M4 12a8 8 0 0 1 14-5.3M20 12a8 8 0 0 1-14 5.3"/><path d="M18 3v4h-4M6 21v-4h4"/>',
        "shield": '<path d="M12 3l7 3v6c0 4.4-3 8-7 9-4-1-7-4.6-7-9V6z"/><path d="M9 12l2 2 4-4"/>',
        "branch": '<circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="8" r="2.5"/><path d="M6 8.5v7M18 10.5c0 3-2.5 4-5.5 4"/>',
        "grid": '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
        "box": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
        "wrench": '<path d="M14.7 6.3a4.5 4.5 0 0 0-6 6L4 17v3h3l4.7-4.7a4.5 4.5 0 0 0 6-6L14 12l-2-2z"/>',
        "monitor": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
        "search": '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l5 5"/>',
        "github": '<path fill="currentColor" stroke="none" d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-.99-.78-.015-.765.915.015 1.545.84 1.76 1.185.945 1.62 2.445 1.17 3.03.885.09-.66.375-1.17.675-1.44-2.67-.3-5.46-1.335-5.46-5.925 0-1.17.42-2.13 1.11-2.88-.12-.3-.48-1.5.105-3.12 0 0 .9-.285 2.955 1.11.87-.24 1.77-.36 2.685-.36.915 0 1.83.12 2.685.36 2.055-1.395 2.955-1.11 2.955-1.11.585 1.62.225 2.82.105 3.12.69.75 1.11 1.71 1.11 2.88 0 4.6-2.79 5.625-5.46 5.925.39.33.72 1.005.72 2.025 0 1.44-.015 2.61-.015 2.955 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>',
        "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
        "check": '<path d="M4 12.5l5 5L20 6.5"/>',
        "terminal": '<path d="M5 7l5 5-5 5M12 17h7"/>',
        "book": '<path d="M4 5a2 2 0 0 1 2-2h14v18H6a2 2 0 0 0-2 2z"/><path d="M4 19a2 2 0 0 1 2-2h14"/>',
        "users": '<circle cx="9" cy="8" r="3.5"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M17.5 14.4c2.1.8 3.5 2.9 3.5 5.6"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
        "chat": '<path d="M21 12a8 8 0 0 1-8 8H4l2.4-2.4A8 8 0 1 1 21 12z"/>',
        "rocket": '<path d="M12 15c-2 0-3-1-3-1s.5-6.5 4-10c2.5 2.5 3.5 6.5 2 11z"/><path d="M9 14l-3 3 1.5.5.5 1.5 3-3M15.5 12.5L18 15l-1.5.5-.5 1.5"/>',
        "zap": '<path d="M13 3L5 13h6l-1 8 8-10h-6z"/>',
        "alert": '<path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17.2v.3"/>',
        "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/>',
        "layers": '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
        "command": '<path d="M9 9V6a3 3 0 1 0-3 3h3zm0 0v6m0-6h6m-6 6v3a3 3 0 1 1-3-3h3zm6-6h3a3 3 0 1 0-3-3v3zm0 6h3a3 3 0 1 1-3 3v-3zm0 0V9"/>',
        "globe": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.3 3.8 5.2 3.8 8.5s-1.3 6.2-3.8 8.5c-2.5-2.3-3.8-5.2-3.8-8.5s1.3-6.2 3.8-8.5z"/>',
        "send": '<path d="M4 12l16-8-6 16-2.5-6z"/><path d="M11.5 14L20 4"/>',
    }
    return ('<svg class="' + cls + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + P[name] + '</svg>')

# ============================================================ 共享 CSS（设计 token 单源）
CSS = r"""
:root{
  --bg:#FAFAFA; --bg-elev:#FFFFFF; --card:#FFFFFF; --card-2:#F4F4F5;
  --line:#E5E7EB; --line-strong:#D1D5DB;
  --text:#111827; --text-2:#6B7280; --text-3:#9CA3AF;
  --ember:#F97316; --ember-hi:#FBBF24; --ember-soft:#EA580C;
  --ember-deep:#C2410C;
  --tint-bg:#FFF7ED; --tint-soft:#FFEDD5; --tint-line:#FED7AA; --tint-edge:#FDBA74;
  --focus-ring:rgba(249,115,22,.15); --glow-a:rgba(249,115,22,.08); --glow-b:rgba(251,191,36,.07);
  --hl-edge:rgba(249,115,22,.55); --term-ember:#FB923C;
  --verified:#16A34A; --link:var(--ember-soft); --warn:#B45309; --danger:#DC2626;
  --grad-brand:linear-gradient(120deg,#EA580C,#F97316);
  --term-bg:#0F172A; --term-bar:#0B1220;
  --mono:ui-monospace,'SF Mono','Cascadia Code','JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace;
  --sans:system-ui,-apple-system,'Segoe UI',Roboto,'PingFang SC','Hiragino Sans GB','Microsoft YaHei','Noto Sans SC',sans-serif;
  --radius:16px; --maxw:1200px; --header-h:64px;
}
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}
  *,*::before,*::after{animation:none!important;transition:none!important}}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);
  font-size:16px;line-height:1.65;-webkit-font-smoothing:antialiased}
img,svg{display:block}
a{color:var(--link);text-decoration:none}
a:hover{text-decoration:underline}
:focus-visible{outline:2px solid var(--ember-soft);outline-offset:2px;border-radius:4px}
.skip-link{position:absolute;left:-999px;top:8px;z-index:200;background:var(--ember);
  color:#fff;padding:8px 14px;border-radius:8px;font-weight:600}
.skip-link:focus{left:8px}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 24px}
.mono{font-family:var(--mono)}
.num{font-variant-numeric:tabular-nums}

/* ---------- 仿样横幅（plain 层必需） ---------- */
.proto-banner{background:var(--tint-bg);color:var(--ember-deep);border-bottom:1px solid var(--tint-line);
  font-size:12.5px;line-height:1.5;padding:7px 24px;text-align:center}
.proto-banner strong{color:var(--ember-deep)}

/* ---------- 头部导航 ---------- */
.site-header{position:sticky;top:0;z-index:100;height:var(--header-h);
  background:rgba(255,255,255,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.header-in{max-width:var(--maxw);margin:0 auto;padding:0 24px;height:100%;
  display:flex;align-items:center;gap:28px}
.logo{display:flex;align-items:center;gap:10px;color:var(--text);font-weight:700;
  font-size:18px;letter-spacing:.2px}
.logo:hover{text-decoration:none}
.logo .logo-mark{width:26px;height:26px;color:var(--ember)}
.logo .logo-mark svg{width:26px;height:26px}
.logo .logo-mark img,.chat-logo img{width:100%;height:100%;object-fit:contain;display:block}
.logo .logo-lockup{display:block;flex:none}
.main-nav{display:flex;gap:4px;margin-left:8px}
.main-nav a{color:var(--text-2);font-size:14.5px;padding:8px 12px;border-radius:8px;
  position:relative;transition:color .16s,background .16s}
.main-nav a:hover{color:var(--text);background:rgba(17,24,39,.05);text-decoration:none}
.main-nav a.active{color:var(--text)}
.main-nav a.active::after{content:"";position:absolute;left:12px;right:12px;bottom:2px;
  height:2px;border-radius:2px;background:var(--grad-brand)}
.header-actions{margin-left:auto;display:flex;align-items:center;gap:12px}
.lang-toggle{display:flex;border:1px solid var(--line-strong);border-radius:999px;overflow:hidden}
.lang-toggle button{background:transparent;border:0;color:var(--text-2);cursor:pointer;
  font-family:var(--mono);font-size:12px;padding:6px 12px;transition:background .16s,color .16s}
.lang-toggle button.on{background:var(--tint-bg);color:var(--ember-deep)}
.icon-btn{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;
  border-radius:8px;border:1px solid var(--line);color:var(--text-2);cursor:pointer;
  background:transparent;transition:color .16s,border-color .16s}
.icon-btn:hover{color:var(--text);border-color:var(--line-strong)}
.gh-btn{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;
  color:var(--text-2);transition:color .16s}
.gh-btn:hover{color:var(--ember)}
.icon-btn svg{width:18px;height:18px}
.gh-btn svg{width:18px;height:18px}
.btn{display:inline-flex;align-items:center;gap:8px;font-weight:600;font-size:14.5px;
  border-radius:9px;padding:10px 18px;cursor:pointer;border:1px solid transparent;
  transition:filter .16s,background .16s,border-color .16s}
.btn svg{width:16px;height:16px}
.btn-primary{background:var(--ember);color:#fff}
.btn-primary:hover{background:var(--ember-soft);text-decoration:none}
.btn-ghost{border-color:var(--line-strong);color:var(--text)}
.btn-ghost:hover{background:rgba(17,24,39,.05);text-decoration:none}
.btn-sm{padding:7px 14px;font-size:13.5px}
.btn-lg{padding:13px 26px;font-size:16px}
.nav-burger{display:none}
.mobile-nav{display:none}

/* ---------- 通用 section ---------- */
.section{padding:88px 0;border-top:1px solid var(--line)}
.section:first-of-type{border-top:0}
.eyebrow{font-family:var(--mono);font-size:12.5px;letter-spacing:.22em;color:var(--ember-soft);
  text-transform:uppercase;display:flex;align-items:center;gap:10px;margin:0 0 14px}
.eyebrow::before{content:"";width:26px;height:1px;background:var(--grad-brand)}
h2.sec-title{font-size:32px;line-height:1.25;margin:0 0 14px;font-weight:700;letter-spacing:-.01em}
.sec-lede{color:var(--text-2);font-size:17px;max-width:640px;margin:0 0 40px}
.grad-text{background:var(--grad-brand);-webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;color:transparent}

/* ---------- Hero ---------- */
.hero{padding:96px 0 72px;border-top:0;
  background:radial-gradient(640px 320px at 88% 8%,var(--glow-a),transparent 70%),
             radial-gradient(520px 280px at 6% 96%,var(--glow-b),transparent 70%)}
.hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:56px;align-items:center}
.hero h1{font-size:50px;line-height:1.18;letter-spacing:-.02em;margin:0 0 22px;font-weight:800}
.hero .lede{color:var(--text-2);font-size:17.5px;max-width:520px;margin:0 0 32px}
.hero-ctas{display:flex;gap:14px;flex-wrap:wrap}

/* ---------- 伪终端 ---------- */
.term{background:var(--term-bg);border:1px solid var(--line-strong);border-radius:var(--radius);
  overflow:hidden;box-shadow:0 8px 24px rgba(15,23,42,.12)}
.term-bar{display:flex;align-items:center;gap:8px;padding:11px 14px;
  border-bottom:1px solid rgba(148,163,184,.16);background:var(--term-bar)}
.term-dot{width:11px;height:11px;border-radius:50%;background:#334155}
.term-dot:nth-child(1){background:#F87171}.term-dot:nth-child(2){background:#FBBF24}
.term-dot:nth-child(3){background:#22C55E}
.term-title{margin-left:8px;font-family:var(--mono);font-size:12px;color:#94A3B8}
.term-body{padding:18px 18px 22px;font-family:var(--mono);font-size:13px;line-height:1.85;
  color:#CBD5E1;overflow-x:auto}
.t-p{color:var(--term-ember)}      /* 提示符 */
.t-c{color:#F1F5F9}      /* 命令 */
.t-o{color:#CBD5E1}      /* 输出 */
.t-dim{color:#64748B}    /* 弱输出 */
.t-ok{color:#4ADE80}     /* 成功 */
.t-w{color:#FBBF24}      /* 等待 */
.t-key{color:#7CB0FF}    /* 关键字 */

/* ---------- 对话面板（AI-Native hero，方案 D） ---------- */
.chat{background:var(--bg-elev);border:1px solid var(--line);border-radius:var(--radius);
  overflow:hidden;box-shadow:0 8px 24px rgba(15,23,42,.08);display:flex;flex-direction:column}
.chat-head{display:flex;align-items:center;gap:10px;padding:13px 16px;border-bottom:1px solid var(--line)}
.chat-logo{width:28px;height:28px;border-radius:8px;background:var(--tint-bg);border:1px solid var(--tint-line);
  color:var(--ember-soft);display:flex;align-items:center;justify-content:center;flex:none}
.chat-logo svg{width:16px;height:16px}
.chat-title{font-family:var(--mono);font-size:12px;color:var(--text-2)}
.chat-body{padding:16px;display:flex;flex-direction:column;gap:12px;min-height:340px}
.bubble{max-width:88%;padding:11px 14px;font-size:13.5px;line-height:1.7;border-radius:14px}
.bubble.user{align-self:flex-end;background:var(--tint-soft);color:var(--ember-deep);border-bottom-right-radius:4px}
.bubble.agent{align-self:flex-start;background:var(--card-2);color:var(--text);border-bottom-left-radius:4px}
.bubble.agent > span{display:block}
.bubble.agent > span.ctx-cards{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0}
.ctx{font-family:var(--mono);font-size:11px;color:var(--ember-deep);background:var(--bg-elev);
  border:1px solid var(--line);border-left:3px solid var(--ember);border-radius:6px;padding:3px 8px}
.typing{display:inline-flex;gap:5px;margin-top:10px;padding:4px 2px}
.typing i{width:7px;height:7px;border-radius:50%;background:var(--ember);opacity:.35;
  animation:typing 1.2s ease-in-out infinite}
.typing i:nth-child(2){animation-delay:.18s}
.typing i:nth-child(3){animation-delay:.36s}
@keyframes typing{0%,60%,100%{opacity:.35;transform:translateY(0)}30%{opacity:1;transform:translateY(-3px)}}
.chat-input{display:flex;gap:10px;padding:12px;border-top:1px solid var(--line);background:var(--card-2)}
.chat-field{position:relative;flex:1;min-width:0;display:flex}
.input-hint{position:absolute;left:13px;top:50%;transform:translateY(-50%);display:flex;align-items:center;gap:7px;
  pointer-events:none;color:var(--t3);font-size:13.5px;white-space:nowrap;transition:opacity .15s}
.input-hint .skill-tag{color:var(--ember);font-weight:600}
.chat-field input:focus~.input-hint,.chat-field input:not(:placeholder-shown)~.input-hint{opacity:0}
.chat-input input{flex:1;min-width:0;background:var(--bg-elev);border:1px solid var(--line-strong);
  border-radius:999px;padding:9px 16px;font-size:13.5px;color:var(--text);outline:0;font-family:var(--sans)}
.chat-input input:focus{border-color:var(--ember);box-shadow:0 0 0 3px var(--focus-ring)}
.chat-send{display:inline-flex;align-items:center;gap:6px;background:var(--ember);color:#fff;border:0;
  border-radius:999px;padding:9px 16px;font-size:13.5px;font-weight:600;cursor:pointer;font-family:var(--sans)}
.chat-send svg{width:14px;height:14px}
.chat-send:hover{background:var(--ember-soft)}

/* ---------- 数据带 ---------- */
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:22px 20px}
.stat .v{font-family:var(--mono);font-size:30px;font-weight:700;letter-spacing:-.02em;
  color:var(--ember)}
.stat .k{color:var(--text-2);font-size:13.5px;margin-top:6px}

/* ---------- 卡片网格 ---------- */
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.grid-2{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:24px;display:flex;flex-direction:column;gap:10px;box-shadow:0 1px 2px rgba(15,23,42,.04);
  transition:border-color .16s,transform .16s,box-shadow .16s}
.card:hover{border-color:var(--line-strong);transform:translateY(-2px);box-shadow:0 4px 6px rgba(15,23,42,.06)}
.card .card-head{display:flex;align-items:center;gap:12px}
.card .card-head h3{margin:0}
.card .card-ic{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;
  justify-content:center;background:var(--tint-bg);color:var(--ember-soft);
  border:1px solid var(--tint-line)}
.card .card-ic svg{width:20px;height:20px}
.card h3{margin:2px 0 0;font-size:17px;font-weight:650}
.card p{margin:0;color:var(--text-2);font-size:14px;line-height:1.6}
.card .card-link{margin-top:auto;font-size:13.5px;color:var(--link);display:inline-flex;
  align-items:center;gap:6px}
.card .card-link svg{width:14px;height:14px}
.card .tagline{display:flex;gap:8px;flex-wrap:wrap;margin-top:2px}
.tag{font-family:var(--mono);font-size:11.5px;color:var(--text-2);border:1px solid var(--line-strong);
  border-radius:999px;padding:2px 10px}
.tag.ember{color:var(--ember-deep);border-color:var(--tint-edge)}
.tag.green{color:#15803D;border-color:#86EFAC}

/* ---------- 痛点 / 对比 ---------- */
.pain{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.pain .card{background:var(--card-2)}
.pain .num-badge{font-family:var(--mono);color:var(--danger);font-size:13px;letter-spacing:.1em}
.answer-strip{margin-top:18px;border:1px dashed var(--tint-edge);border-radius:var(--radius);
  padding:18px 22px;color:var(--text-2);font-size:15px;background:var(--tint-bg)}
.answer-strip strong{color:var(--text)}

.cmp{width:100%;border-collapse:collapse;font-size:14.5px;border:1px solid var(--line);
  border-radius:var(--radius);overflow:hidden}
.cmp th,.cmp td{padding:13px 18px;text-align:left;border-bottom:1px solid var(--line);
  vertical-align:top}
.cmp thead th{background:var(--bg-elev);color:var(--text);font-size:13.5px;
  font-family:var(--mono);letter-spacing:.05em}
.cmp thead th.col-fenix{color:var(--ember-soft)}
.cmp td:first-child{color:var(--text);white-space:nowrap;font-weight:600}
.cmp td{color:var(--text-2)}
.cmp td.col-fenix{color:var(--text);background:var(--tint-bg)}
.cmp tr:last-child td{border-bottom:0}
.cmp .yes{color:var(--verified)}
.cmp .no{color:var(--danger)}

/* ---------- 循环图 ---------- */
.loop-diagram{display:grid;grid-template-columns:repeat(13,auto);align-items:stretch;
  justify-content:center;gap:0}
.loop-node{background:var(--card);border:1px solid var(--line-strong);border-radius:10px;
  padding:12px 13px;min-width:0;text-align:center}
.loop-node .t{font-weight:650;font-size:13.5px;white-space:nowrap}
.loop-node .d{font-family:var(--mono);font-size:10.5px;color:var(--text-3);margin-top:4px;white-space:nowrap}
.loop-node.hl{border-color:var(--term-ember);background:var(--tint-bg)}
.loop-node.gate{border-color:rgba(34,197,94,.5)}
.loop-arrow{display:flex;align-items:center;color:var(--text-3);padding:0 6px}
.loop-arrow svg{width:20px;height:20px}
.loop-back{margin-top:16px;text-align:center;font-family:var(--mono);font-size:12.5px;
  color:var(--warn);display:flex;align-items:center;justify-content:center;gap:8px}
.loop-back svg{width:16px;height:16px}

/* ---------- 状态机 chips ---------- */
.state-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.st{font-family:var(--mono);font-size:12.5px;padding:5px 12px;border-radius:999px;
  border:1px solid var(--line-strong);color:var(--text-2);background:var(--card)}
.st.done{border-color:rgba(34,197,94,.5);color:var(--verified)}
.st.hl{border-color:var(--hl-edge);color:var(--ember-soft)}
.st-risk{border-color:rgba(245,158,11,.5);color:var(--warn)}
.state-sep{color:var(--text-3);font-size:13px}

/* ---------- 架构分层 ---------- */
.arch{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.arch-col{background:var(--card-2);border:1px solid var(--line);border-radius:var(--radius);
  padding:20px;display:flex;flex-direction:column;gap:10px}
.arch-col h4{margin:0;font-size:13px;font-family:var(--mono);letter-spacing:.14em;
  color:var(--ember-soft);text-transform:uppercase}
.arch-item{border:1px solid var(--line);border-radius:8px;padding:10px 14px;
  background:var(--card);font-size:13.5px;color:var(--text-2)}
.arch-item b{color:var(--text);font-weight:600;display:block;font-size:14px;margin-bottom:2px}

/* ---------- 文档页 ---------- */
.doc-search{display:flex;align-items:center;gap:12px;background:var(--card);
  border:1px solid var(--line-strong);border-radius:12px;padding:14px 18px;max-width:720px}
.doc-search svg{width:20px;height:20px;color:var(--text-3);flex:none}
.doc-search input{flex:1;background:transparent;border:0;outline:0;color:var(--text);
  font-size:15.5px;font-family:var(--sans)}
.doc-search input::placeholder{color:var(--text-3)}
.doc-search kbd{font-family:var(--mono);font-size:11.5px;color:var(--text-3);
  border:1px solid var(--line-strong);border-radius:6px;padding:3px 8px;white-space:nowrap}
.path-row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:56px}
.path-card{position:relative;background:var(--card-2);border:1px solid var(--line);
  border-radius:var(--radius);padding:22px}
.path-card .step{font-family:var(--mono);font-size:12px;color:var(--ember-soft);letter-spacing:.18em}
.path-card h3{margin:8px 0 6px;font-size:17px}
.path-card p{margin:0;color:var(--text-2);font-size:14px}
.card-featured{grid-column:1/-1;display:grid;grid-template-columns:1.05fr .95fr;gap:26px;align-items:start}
.card-featured .card-body{display:flex;flex-direction:column;gap:10px;min-width:0}
.card-shot{margin:0;border:1px solid var(--line-strong);border-radius:12px;overflow:hidden;box-shadow:0 6px 18px rgba(15,23,42,.10);background:var(--card)}
.card-shot img{width:100%;display:block;aspect-ratio:16/9;object-fit:cover;object-position:top left}
.card-shot figcaption{font-family:var(--mono);font-size:11px;color:var(--text-3);padding:7px 12px;border-top:1px solid var(--line);background:var(--card-2)}
@media(max-width:920px){.card-featured{grid-template-columns:1fr}}
.card-featured h3{white-space:nowrap}
.card-shot img{cursor:zoom-in}
.caps-grid{grid-template-columns:repeat(auto-fit,minmax(520px,1fr));grid-auto-flow:dense}
.caps-grid > .card:not(.card-featured){min-width:0}
/* mode 两卡：上下堆叠各占整行，icon+标题同行 */
.mode-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.mode-grid .card .card-head{margin-bottom:10px}
.mode-grid .card p{max-width:75ch;margin-bottom:14px}

.lc-figure{margin:26px 0 0;border:1px solid var(--line-strong);border-radius:16px;background:var(--card);box-shadow:0 6px 18px rgba(15,23,42,.08);overflow:hidden}
.lc-figure svg{display:block;width:92%;height:auto;margin:0 auto}
.lc-figure figcaption{font-family:var(--mono);font-size:11px;color:var(--text-3);padding:8px 14px;border-top:1px solid var(--line);background:var(--card-2)}
.lb{position:fixed;inset:0;z-index:300;background:rgba(11,17,32,.92);display:flex;align-items:center;justify-content:center;cursor:zoom-out;padding:4vh 4vw}
.lb img{max-width:92vw;max-height:88vh;border-radius:10px;box-shadow:0 20px 60px rgba(0,0,0,.5);background:#fff}
.lb-hint{position:absolute;bottom:3vh;left:0;right:0;text-align:center;color:#cbd5e1;font-family:var(--mono);font-size:12px}
.hero-split{display:grid;grid-template-columns:1.1fr .9fr;gap:40px;align-items:center}
.hero-vis{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.hv-card{display:flex;flex-direction:column;gap:6px;background:var(--card);border:1px solid var(--line);
  border-radius:12px;padding:16px 18px;text-decoration:none;transition:border-color .16s,transform .16s}
.hv-card:hover{border-color:var(--ember);transform:translateY(-2px)}
.hv-ic{width:30px;height:30px;border-radius:8px;background:var(--tint-bg);color:var(--ember);
  display:inline-flex;align-items:center;justify-content:center}
.hv-head{display:flex;align-items:center;gap:10px}
.hv-d{font-size:12.5px;color:var(--text-2);line-height:1.5}
.hv-t{font-weight:650;font-size:14.5px;color:var(--text)}
.hv-n{font-family:var(--mono);font-size:11.5px;color:var(--text-3)}
@media(max-width:920px){.hero-split{grid-template-columns:1fr}
  .loop-diagram{grid-template-columns:repeat(7,auto);row-gap:12px;justify-content:center}}
.grp-head{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin:0 0 18px}
.grp-head h3{display:flex;align-items:center;gap:10px;font-size:16px;margin:0}
.grp-lede{color:var(--text-2);font-size:14px}
.doc-group{margin-bottom:44px}
.doc-group h3{display:flex;align-items:center;gap:10px;font-size:16px;margin:0 0 14px}
.grp-head .cnt{font-family:var(--mono);font-size:12px;color:var(--text-3);
  border:1px solid var(--line-strong);border-radius:999px;padding:1px 9px;white-space:nowrap}
.doc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.doc-card{display:block;background:var(--card);border:1px solid var(--line);
  border-radius:9px;padding:16px 18px;color:var(--text);
  transition:border-color .16s,transform .16s}
.doc-card:hover{border-color:var(--line-strong);transform:translateY(-2px);text-decoration:none}
.doc-card .no{font-family:var(--mono);font-size:11.5px;color:var(--text-3)}
.doc-card .tt{font-weight:650;font-size:14.5px;margin:3px 0 4px}
.doc-card .ds{color:var(--text-2);font-size:13px;line-height:1.55}

/* ---------- 社区页 ---------- */
.gh-card{display:grid;grid-template-columns:1.2fr .8fr;gap:16px;align-items:stretch}
.gh-main{background:var(--card);border:1px solid var(--line-strong);border-radius:var(--radius);
  padding:26px}
.gh-main .repo{display:flex;align-items:center;gap:12px;font-family:var(--mono);
  font-size:17px;font-weight:600}
.gh-main .repo svg{width:22px;height:22px;color:var(--text-2)}
.gh-stats{display:flex;gap:26px;margin:18px 0}
.gh-stats .s .v{font-family:var(--mono);font-size:22px;font-weight:700}
.gh-stats .s .k{font-size:12.5px;color:var(--text-2)}
.gh-side{display:flex;flex-direction:column;gap:12px}
.mini-card{background:var(--card-2);border:1px solid var(--line);border-radius:var(--radius);
  padding:18px;display:flex;gap:12px;align-items:flex-start}
.mini-card .card-ic{flex:none;width:34px;height:34px;border-radius:9px;background:var(--tint-bg);
  color:var(--ember-soft);display:flex;align-items:center;justify-content:center;
  border:1px solid var(--tint-line)}
.mini-card .card-ic svg{width:17px;height:17px}
.mini-card h4{margin:0 0 3px;font-size:14.5px}
.mini-card p{margin:0;color:var(--text-2);font-size:13px}
.chan-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.roadmap-item{display:flex;gap:16px;padding:16px 0;border-bottom:1px solid var(--line)}
.roadmap-item:last-child{border-bottom:0}
.roadmap-item .ver{font-family:var(--mono);font-size:13px;color:var(--ember-soft);
  min-width:86px;padding-top:2px}
.roadmap-item .bd h4{margin:0 0 3px;font-size:14.5px;font-weight:600}
.roadmap-item .bd p{margin:0;color:var(--text-2);font-size:13.5px}

/* ---------- CTA 带 ---------- */
.cta-band{border-radius:var(--radius);padding:44px 40px;margin-top:28px;
  background:linear-gradient(180deg,var(--tint-bg),#FFFFFF)}
.cta-band h2{margin:0 0 10px;font-size:26px}
.cta-band p{margin:0 0 24px;color:var(--text-2);font-size:15.5px}
.cta-band .hero-ctas{margin:0}

/* ---------- 页脚 ---------- */
.site-footer{border-top:1px solid var(--line);background:var(--bg-elev);padding:56px 0 32px;
  margin-top:0}
.foot-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr 1fr;gap:32px}
.foot-brand p{color:var(--text-2);font-size:13.5px;max-width:260px;margin:12px 0 0}
.foot-col h4{font-size:13px;font-family:var(--mono);letter-spacing:.16em;color:var(--text-3);
  text-transform:uppercase;margin:0 0 14px}
.foot-col a{display:block;color:var(--text-2);font-size:14px;padding:5px 0}
.ft-disabled{display:block;color:var(--text-3);font-size:14px;padding:5px 0;cursor:not-allowed}
.foot-col a:hover{color:var(--text)}
.foot-bottom{margin-top:44px;padding-top:22px;border-top:1px solid var(--line);
  display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;
  color:var(--text-3);font-size:13px}

/* ---------- 响应式 ---------- */
@media (max-width:1024px){
  .hero-grid{grid-template-columns:1fr;gap:40px}
  .hero h1{font-size:40px}
  .grid-4{grid-template-columns:repeat(2,1fr)}
  .stats{grid-template-columns:repeat(3,1fr)}
  .foot-grid{grid-template-columns:1fr 1fr 1fr}
  .main-nav{display:none}
  .nav-burger{display:inline-flex}
  .mobile-nav{display:none;position:fixed;top:var(--header-h);left:0;right:0;z-index:99;
    background:var(--bg-elev);border-bottom:1px solid var(--line);padding:12px 24px 18px}
  .mobile-nav.open{display:block}
  .mobile-nav a{display:block;padding:12px 4px;color:var(--text-2);font-size:16px;
    border-bottom:1px solid var(--line)}
  .mobile-nav a:last-child{border-bottom:0}
}
@media (max-width:768px){
  .section{padding:64px 0}
  .hero{padding:64px 0 48px}
  .hero h1{font-size:33px}
  h2.sec-title{font-size:26px}
  .grid-3,.pain,.arch,.path-row{grid-template-columns:1fr}
  .caps-grid{grid-template-columns:1fr}
  .mode-grid{grid-template-columns:1fr}
  .grid-4,.doc-grid,.chan-grid{grid-template-columns:repeat(2,1fr)}
  .stats{grid-template-columns:repeat(2,1fr)}
  .gh-card{grid-template-columns:1fr}
  .cmp{font-size:13px}
  .cmp th,.cmp td{padding:10px 10px}
  .header-actions .btn{display:none}
}
@media (max-width:480px){
  .grid-4,.doc-grid,.chan-grid,.stats{grid-template-columns:1fr}
  .cta-band{padding:30px 22px}
  .foot-grid{grid-template-columns:1fr 1fr}
}

/* ---------- palette dock & themes ---------- */
.pal-dock{position:fixed;left:16px;bottom:16px;z-index:80;display:flex;align-items:center;gap:8px;
  background:var(--bg-elev);border:1px solid var(--line);border-radius:999px;padding:7px 12px;
  box-shadow:0 6px 18px rgba(17,24,39,.10)}
.pal-dock .pal-cap{font-size:11px;color:var(--text-3);margin-right:2px}
.pal-dot{width:18px;height:18px;border-radius:50%;border:2px solid transparent;padding:0;cursor:pointer;
  appearance:none;background-clip:padding-box;flex:none}
.pal-dot.on{border-color:var(--text);box-shadow:inset 0 0 0 2px var(--bg-elev)}
.pal-dot.p-ember{background:linear-gradient(120deg,#EA580C,#F97316)}
.pal-dot.p-violet{background:linear-gradient(120deg,#7C3AED,#8B5CF6)}
.pal-dot.p-orchid{background:linear-gradient(120deg,#9C2F81,#B8409A)}
.pal-dot.p-royal{background:linear-gradient(120deg,#5B21B6,#6D28D9)}
.pal-dot.p-aurora{background:linear-gradient(120deg,#0891B2,#8B5CF6)}
.pal-dot.p-orchid-aurora{background:linear-gradient(135deg,#B8409A 0%,#8B5CF6 50%,#0891B2 100%)}
body[data-palette="violet"]{--ember:#8B5CF6;--ember-soft:#7C3AED;--ember-deep:#6D28D9;
  --tint-bg:#F5F3FF;--tint-soft:#EDE9FE;--tint-line:#DDD6FE;--tint-edge:#C4B5FD;
  --focus-ring:rgba(139,92,246,.15);--glow-a:rgba(139,92,246,.08);--glow-b:rgba(196,181,253,.07);
  --hl-edge:rgba(139,92,246,.55);--term-ember:#A78BFA;
  --grad-brand:linear-gradient(120deg,#7C3AED,#8B5CF6);--link:#7C3AED}
body[data-palette="orchid"]{--ember:#B8409A;--ember-soft:#9C2F81;--ember-deep:#83286B;
  --tint-bg:#FDF2F8;--tint-soft:#FCE7F3;--tint-line:#FBCFE8;--tint-edge:#F9A8D4;
  --focus-ring:rgba(184,64,154,.15);--glow-a:rgba(184,64,154,.08);--glow-b:rgba(249,168,212,.07);
  --hl-edge:rgba(184,64,154,.55);--term-ember:#DA8BC4;
  --grad-brand:linear-gradient(120deg,#9C2F81,#B8409A);--link:#9C2F81}
body[data-palette="royal"]{--ember:#6D28D9;--ember-soft:#5B21B6;--ember-deep:#4C1D95;
  --tint-bg:#F5F3FF;--tint-soft:#EDE9FE;--tint-line:#C4B5FD;--tint-edge:#A78BFA;
  --focus-ring:rgba(109,40,217,.15);--glow-a:rgba(109,40,217,.08);--glow-b:rgba(167,139,250,.07);
  --hl-edge:rgba(109,40,217,.55);--term-ember:#C4B5FD;
  --grad-brand:linear-gradient(120deg,#5B21B6,#7C3AED);--link:#6D28D9}
body[data-palette="aurora"]{--ember:#8B5CF6;--ember-soft:#7C3AED;--ember-deep:#6D28D9;
  --tint-bg:#F5F3FF;--tint-soft:#EDE9FE;--tint-line:#DDD6FE;--tint-edge:#C4B5FD;
  --focus-ring:rgba(139,92,246,.15);--glow-a:rgba(8,145,178,.08);--glow-b:rgba(139,92,246,.07);
  --hl-edge:rgba(8,145,178,.55);--term-ember:#67E8F9;
  --grad-brand:linear-gradient(120deg,#0891B2,#8B5CF6);--link:#0E7490}
body[data-palette="orchid-aurora"]{--ember:#B8409A;--ember-soft:#9C2F81;--ember-deep:#83286B;
  --tint-bg:#FDF2F8;--tint-soft:#FCE7F3;--tint-line:#FBCFE8;--tint-edge:#F9A8D4;
  --focus-ring:rgba(184,64,154,.15);--glow-a:rgba(8,145,178,.08);--glow-b:rgba(184,64,154,.07);
  --hl-edge:rgba(184,64,154,.55);--term-ember:#E879C8;
  --grad-brand:linear-gradient(120deg,#0891B2 0%,#8B5CF6 48%,#B8409A 100%);--link:#0E7490}
body[data-palette="ember"]{--ember:#F97316;--ember-soft:#EA580C;--ember-deep:#C2410C;
  --tint-bg:#FFF7ED;--tint-soft:#FFEDD5;--tint-line:#FED7AA;--tint-edge:#FDBA74;
  --focus-ring:rgba(249,115,22,.15);--glow-a:rgba(249,115,22,.08);--glow-b:rgba(251,191,36,.07);
  --hl-edge:rgba(249,115,22,.55);--term-ember:#FB923C;
  --grad-brand:linear-gradient(120deg,#EA580C,#F97316);--link:#EA580C}
@media (max-width:768px){.pal-dock{left:10px;bottom:10px;padding:5px 8px;gap:6px}
  .pal-dock .pal-cap{display:none}.pal-dot{width:15px;height:15px}}
"""

# ============================================================ 页面外壳
def shell(page_id, title_zh, active, content_html, i18n, nav_extra=""):
    i18n_json = json.dumps(i18n, ensure_ascii=False)
    favicon = "logo-64.png"
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-page="{page_id}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_zh}</title>
<link rel="icon" href="{favicon}">
<style>{CSS}</style>
</head>
<body data-palette="orchid-aurora">
<a class="skip-link" href="#main" data-i18n="a11y.skip">跳到主内容</a>
<div class="proto-banner" data-proto-id="{page_id}-proto-banner"><strong>仿样原型 · 视觉参照、无约束力</strong> ， 本原型为纯 HTML/CSS 仿样级（栈画像 unknown，纯静态站点无组件库），批准后仅作视觉参照；约束力由 SPEC 的 DESIGN.md 承载</div>
<header class="site-header" data-proto-id="{page_id}-header">
  <div class="header-in">
    <a class="logo" href="index.html" data-proto-id="{page_id}-logo">
      <span class="logo-mark"><img src="logo-64.png" alt=""></span><svg class="logo-lockup" width="124" height="38" viewBox="0 0 124 38" role="img" aria-label="Fenix Harness, The AI-Native SDLC"><text x="0" y="17" textLength="117.3" lengthAdjust="spacing" font-family="Montserrat,-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif" font-size="12.5px" font-weight="600" letter-spacing="1px" fill="var(--text)">FENIX <tspan font-weight="500" fill="var(--text-2)">HARNESS</tspan></text><text x="0" y="30.5" textLength="117.3" lengthAdjust="spacing" font-family="Montserrat,-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif" font-size="9px" font-weight="500" letter-spacing="2.2px" fill="var(--text-3)">THE AI-NATIVE SDLC</text></svg>
    </a>
    <nav class="main-nav" data-proto-id="{page_id}-nav" aria-label="主导航">
      <a href="index.html" data-i18n="nav.home"{' class="active"' if active == 'index' else ''}>首页</a>
      <a href="index.html#quickstart" data-i18n="nav.quick"{' class="active"' if active == 'quick' else ''}>快速开始</a>
      <a href="why.html" data-i18n="nav.why"{' class="active"' if active == 'why' else ''}>使用场景</a>
      <a href="capabilities.html" data-i18n="nav.capabilities"{' class="active"' if active == 'capabilities' else ''}>能力全景</a>
      <a href="docs.html" data-i18n="nav.docs"{' class="active"' if active == 'docs' else ''}>文档</a>
      <a href="community.html" data-i18n="nav.community"{' class="active"' if active == 'community' else ''}>社区</a>
    </nav>
    <div class="header-actions">
      <div class="lang-toggle" data-proto-id="nav-lang-toggle" role="group" aria-label="语言切换">
        <button type="button" id="lang-zh" class="on">中文</button>
        <button type="button" id="lang-en">EN</button>
      </div>
      <a class="gh-btn" href="https://github.com/fenixsoft/fenixd" aria-label="GitHub" data-proto-id="{page_id}-github-btn">{icon("github")}</a>

      <button type="button" class="icon-btn nav-burger" id="nav-burger" aria-label="打开菜单" aria-expanded="false">{icon("grid")}</button>
    </div>
  </div>
</header>
<nav class="mobile-nav" id="mobile-nav" data-proto-id="{page_id}-mobile-nav" aria-label="移动端导航">
  <a href="index.html" data-i18n="nav.home">首页</a>
  <a href="index.html#quickstart" data-i18n="nav.quick">快速开始</a>
  <a href="why.html" data-i18n="nav.why">使用场景</a>
  <a href="capabilities.html" data-i18n="nav.capabilities">能力全景</a>
  <a href="docs.html" data-i18n="nav.docs">文档</a>
  <a href="community.html" data-i18n="nav.community">社区</a>
</nav>
<main id="main">
{content_html}
</main>
<footer class="site-footer" data-proto-id="{page_id}-footer">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-brand">
        <a class="logo" href="index.html"><span class="logo-mark"><img src="logo-64.png" alt=""></span><span>Fenixd</span></a>
        <p data-i18n="footer.brand">Fenix Loop Engineering Framework，把「写软件」编排成受控闭环：实现、独立验证、打回修复，质量由循环收敛保证。</p>
      </div>
      <div class="foot-col" data-proto-id="{page_id}-footer-product">
        <h4 data-i18n="footer.product">产品</h4>
        <a href="why.html" data-i18n="footer.p1">为什么是 Fenixd</a>
        <a href="capabilities.html" data-i18n="footer.p2">能力全景</a>
        <a href="https://github.com/fenixsoft/fenixd/releases" data-i18n="footer.p3">更新日志</a>
        <span class="ft-disabled" data-i18n="footer.p4">路线图</span>
      </div>
      <div class="foot-col" data-proto-id="{page_id}-footer-docs">
        <h4 data-i18n="footer.docs">文档</h4>
        <a href="docs.html" data-i18n="footer.d1">快速上手</a>
        <a href="docs.html" data-i18n="footer.d2">核心概念与架构</a>
        <a href="docs.html" data-i18n="footer.d3">CLI 操作手册</a>
        <a href="docs.html" data-i18n="footer.d4">FAQ 与故障排查</a>
      </div>
      <div class="foot-col" data-proto-id="{page_id}-footer-community">
        <h4 data-i18n="footer.community">社区</h4>
        <a href="https://github.com/fenixsoft/fenixd" data-i18n="footer.c1">GitHub</a>
        <a href="https://github.com/fenixsoft/fenixd/discussions" data-i18n="footer.c2">Discussions</a>
        <a href="https://github.com/fenixsoft/fenixd/issues" data-i18n="footer.c3">问题反馈</a>
        <a href="https://github.com/fenixsoft/fenixd/blob/main/docs/help/14-contributing.md" data-i18n="footer.c4">贡献指南</a>
      </div>
      <div class="foot-col" data-proto-id="{page_id}-footer-about">
        <h4 data-i18n="footer.about">关于</h4>
        <a href="https://icyfenix.cn" data-i18n="footer.a1">博客</a>
        <a href="mailto:icyfenix@gmail.com" data-i18n="footer.a2">联系</a>
      </div>
    </div>
    <div class="foot-bottom">
      <span data-i18n="footer.legal">© 2026 Fenixd · Fenix Loop Engineering Framework</span>
      <span class="mono" data-i18n="footer.dogfood">Fenixd 由 Fenixd 自动开发，本站亦然</span>
    </div>
  </div>
</footer>
<div class="pal-dock" data-proto-id="{page_id}-palette-dock" role="group" aria-label="配色方案切换（原型比选用）">
  <span class="pal-cap">配色</span>
  <button type="button" class="pal-dot p-ember" data-pal="ember" data-i18n-title="pal.ember" data-i18n-label="pal.ember" aria-label="余烬橙"></button>
  <button type="button" class="pal-dot p-violet" data-pal="violet" data-i18n-title="pal.violet" data-i18n-label="pal.violet" aria-label="紫罗兰"></button>
  <button type="button" class="pal-dot p-orchid" data-pal="orchid" data-i18n-title="pal.orchid" data-i18n-label="pal.orchid" aria-label="品红梅"></button>
  <button type="button" class="pal-dot p-royal" data-pal="royal" data-i18n-title="pal.royal" data-i18n-label="pal.royal" aria-label="深靛紫"></button>
  <button type="button" class="pal-dot p-aurora" data-pal="aurora" data-i18n-title="pal.aurora" data-i18n-label="pal.aurora" aria-label="极光紫青"></button>
  <button type="button" class="pal-dot p-orchid-aurora on" data-pal="orchid-aurora" data-i18n-title="pal.orchid-aurora" data-i18n-label="pal.orchid-aurora" aria-label="品红极光"></button>
</div>

<script>
window.PROTO_I18N = {i18n_json};
(function () {{
  var dict = window.PROTO_I18N;
  function apply(lang) {{
    var pack = dict[lang] || {{}};
    document.documentElement.lang = lang === 'en' ? 'en' : 'zh-CN';
    if (pack.title) document.title = pack.title;
    document.querySelectorAll('[data-i18n]').forEach(function (el) {{
      var k = el.getAttribute('data-i18n');
      if (pack[k] !== undefined) el.innerHTML = pack[k];
    }});
    document.querySelectorAll('[data-i18n-ph]').forEach(function (el) {{
      var k = el.getAttribute('data-i18n-ph');
      if (pack[k] !== undefined) el.setAttribute('placeholder', pack[k]);
    }});
    document.querySelectorAll('[data-i18n-title]').forEach(function (el) {{
      var k = el.getAttribute('data-i18n-title');
      if (pack[k] !== undefined) el.setAttribute('title', pack[k]);
    }});
    document.querySelectorAll('[data-i18n-label]').forEach(function (el) {{
      var k = el.getAttribute('data-i18n-label');
      if (pack[k] !== undefined) el.setAttribute('aria-label', pack[k]);
    }});
    document.getElementById('lang-zh').classList.toggle('on', lang === 'zh');
    document.getElementById('lang-en').classList.toggle('on', lang === 'en');
    try {{ localStorage.setItem('fenixd-proto-lang', lang); }} catch (e) {{}}
  }}
  document.getElementById('lang-zh').addEventListener('click', function () {{ apply('zh'); }});
  document.getElementById('lang-en').addEventListener('click', function () {{ apply('en'); }});
  var saved = 'zh';
  try {{ saved = localStorage.getItem('fenixd-proto-lang') || 'zh'; }} catch (e) {{}}
  apply(saved);
  var burger = document.getElementById('nav-burger');
  if (burger) burger.addEventListener('click', function () {{
    var m = document.getElementById('mobile-nav');
    var open = m.classList.toggle('open');
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
  }});
  var PAL_DOCK = document.querySelector('.pal-dock');
  if (PAL_DOCK) {{
    var dots = PAL_DOCK.querySelectorAll('.pal-dot');
    var setPal = function (v, save) {{
      document.body.setAttribute('data-palette', v);
      dots.forEach(function (d) {{ d.classList.toggle('on', d.getAttribute('data-pal') === v); }});
      if (save) {{ try {{ localStorage.setItem('fenixd-proto-palette', v); }} catch (e) {{}} }}
    }};
    var sp = 'orchid-aurora';
    try {{ sp = localStorage.getItem('fenixd-proto-palette') || 'orchid-aurora'; }} catch (e) {{}}
    if (sp !== 'orchid-aurora') setPal(sp, false);
    dots.forEach(function (d) {{ d.addEventListener('click', function () {{ setPal(d.getAttribute('data-pal'), true); }}); }});
  }}
}})();
</script>
<script>
(function(){{
  var shots = document.querySelectorAll('.card-shot img');
  if (!shots.length) return;
  var lb = document.createElement('div');
  lb.className = 'lb'; lb.style.display = 'none';
  lb.innerHTML = '<img alt=""><div class="lb-hint">ESC / click to close · 点击关闭</div>';
  document.body.appendChild(lb);
  var big = lb.querySelector('img');
  shots.forEach(function(img){{
    img.addEventListener('click', function(){{
      big.src = img.src; lb.style.display = 'flex';
    }});
  }});
  lb.addEventListener('click', function(){{ lb.style.display = 'none'; }});
  document.addEventListener('keydown', function(e){{
    if (e.key === 'Escape') lb.style.display = 'none';
  }});
}})();
</script>
<script src="annotator.js" defer></script>
</body>
</html>
"""

# ============================================================ 公共 i18n 键
COMMON_ZH = {
    "a11y.skip": "跳到主内容",
    "nav.home": "首页", "nav.quick": "快速开始", "nav.why": "使用场景", "nav.capabilities": "能力全景",
    "nav.docs": "文档", "nav.community": "社区", "nav.cta": "快速开始",
    "footer.brand": "Fenix Loop Engineering Framework，把「写软件」编排成受控闭环：实现、独立验证、打回修复，质量由循环收敛保证。",
    "footer.product": "产品", "footer.p1": "为什么是 Fenixd", "footer.p2": "能力全景",
    "footer.p3": "更新日志", "footer.p4": "路线图",
    "footer.docs": "文档", "footer.d1": "快速上手", "footer.d2": "核心概念与架构",
    "footer.d3": "CLI 操作手册", "footer.d4": "FAQ 与故障排查",
    "footer.community": "社区", "footer.c1": "GitHub", "footer.c2": "Discussions",
    "footer.c3": "问题反馈", "footer.c4": "贡献指南",
    "footer.about": "关于", "footer.a1": "博客", "footer.a2": "联系",
    "footer.legal": "© 2026 Fenixd · Fenix Loop Engineering Framework",
    "footer.dogfood": "Fenixd 由 Fenixd 自动开发，本站亦然",
    "pal.ember": "余烬橙", "pal.violet": "紫罗兰", "pal.orchid": "品红梅", "pal.royal": "深靛紫", "pal.aurora": "极光紫青",
    "pal.orchid-aurora": "品红极光（当前默认 · 品红梅 × 极光紫青）",
}
COMMON_EN = {
    "a11y.skip": "Skip to content",
    "nav.home": "Home", "nav.quick": "Quick Start", "nav.why": "Why Fenixd", "nav.capabilities": "Capabilities",
    "nav.docs": "Docs", "nav.community": "Community", "nav.cta": "Get Started",
    "footer.brand": "Fenix Loop Engineering Framework, software development as a controlled loop: implement, verify independently, bounce back and fix. Quality converges through the loop.",
    "footer.product": "Product", "footer.p1": "Why Fenixd", "footer.p2": "Capabilities",
    "footer.p3": "Changelog", "footer.p4": "Roadmap",
    "footer.docs": "Docs", "footer.d1": "Quick Start", "footer.d2": "Concepts &amp; Architecture",
    "footer.d3": "CLI Handbook", "footer.d4": "FAQ &amp; Troubleshooting",
    "footer.community": "Community", "footer.c1": "GitHub", "footer.c2": "Discussions",
    "footer.c3": "Report an Issue", "footer.c4": "Contributing",
    "footer.about": "About", "footer.a1": "Blog", "footer.a2": "Contact",
    "footer.legal": "© 2026 Fenixd · Fenix Loop Engineering Framework",
    "footer.dogfood": "Fenixd is developed by Fenixd itself, so is this site",
    "pal.ember": "Ember", "pal.violet": "Violet", "pal.orchid": "Orchid", "pal.royal": "Royal Purple", "pal.aurora": "Aurora Duo",
    "pal.orchid-aurora": "Orchid Aurora (current default · orchid × aurora)",
}

def merge_common(d):
    out = dict(COMMON_ZH); out.update(d); return out
def merge_common_en(d):
    out = dict(COMMON_EN); out.update(d); return out

# ============================================================ 页面 1：index.html
def page_index():
    zh = merge_common({
        "title": "Fenixd · 让软件开发规格驱动、循环验证、自动交付",
        "hero.eyebrow": "FENIX AI-NATIVE SDLC DEVELOPMENT",
        "hero.h1": 'AI Native 的软件开发<br><span class="grad-text">规格驱动。循环验证。自动交付。</span>',
        "hero.lede": "Fenixd 是 Harness 中立的自动化软件开发循环框架，支持 Claude Code、DSH 等多种 Harness。它把自然语言需求沉淀为 SPEC，经「实现 → 独立验证 → 打回修复」的受控闭环，交付<strong>已实现、已验证、可上线</strong>的代码，全程无需人工介入，唯一的人工门禁是最终审批推送。",
        "hero.cta1": "什么是 Fenixd", "hero.cta2": "快速开始",
        "chat.title": "Fenixd, 一句话需求，对话式交付",
        "chat.u1": "给用户中心加邮箱登录，要能禁用密码登录",
        "chat.a1": "已澄清意图，完整 SPEC 已经生成：proposal、design、specs、tasks 四份俱全，建议执行模式 full。",
        "chat.a2": "评审通过后 daemon 自动拾取，在独立 worktree 里实现全部 14 个任务，循环验证跑完 6 个场景零 LLM 全部通过。",
        "chat.a3": "状态已到 done，自动交付只差最后一步：等你审批推送，这是全流程唯一的人工门禁。",
        "chat.k1": "/fenix-new", "chat.k2": "说出你的下一个需求…", "chat.send": "发送",
        "stats.title": "数字里的 Fenixd", "stats.lede": "Fenixd 自身的演进由 Fenixd 驱动，这些是本仓库的真实运转口径（原型页均为示例数据）。",
        "cap.eyebrow": "WHAT PROBLEM FENIXD SOLVES", "cap.title": "Fenixd 的设计意图",
        "cap.lede": "AI 让写代码快了十倍，也让软件熵增快了十倍。当生成速度超过理解与验证的速度，混乱开始加速累积：新功能不断上线，旧功能却在悄悄损坏。Fenixd 用四类机制对抗熵增，SPEC 驱动、循环验证、质量门禁、知识蒸馏，把约束从「口头指南」升级为机器执行的「硬闸门」。",
        "q.eyebrow": "QUICKSTART", "q.title": "三步接入，把循环跑起来",
        "q.lede": "无需数据库、无需常驻服务集群，全部状态落在仓库的普通文件上。",
        "ev.lede": "代码由 daemon 自动交付、循环验证；每一个 SPEC 的流转、每一次 Agent 的动作都在 Dashboard 上实时可见。",
        "ev.c1": "SPEC 流转：从一句话需求到审批推送，状态一目了然",
        "ev.c2": "Command Center：12 类 Agent 的实例、成功率与今日活动",
        "ev.c3": "活动流：谁在何时读了什么、改了什么、为什么决策",
        "g.eyebrow": "DOCS PREVIEW", "g.title": "从快速上手到深度治理",
        "g.lede": "12 篇专题 + 3 篇手册构成的帮助文档体系，与 Dashboard「帮助」菜单同源。",
        "dog.title": "Fenixd 由 Fenixd 开发",
        "dog.lede": "本仓库已全自动推进 500+ 个 SPEC（实现 → 验证 → 打回修复 → 推送），是这套框架最直接的实战验证，包括你正在看的这个官网。",
        "dog.cta1": "看看它是怎么运转的", "dog.cta2": "访问 GitHub",
    })
    en = merge_common_en({
        "title": "Fenixd · Spec-driven. Loop-verified. Automated.",
        "hero.eyebrow": "FENIX AI-NATIVE SDLC DEVELOPMENT",
        "hero.h1": 'AI-native software development,<br><span class="grad-text">spec-driven. loop-verified. automated.</span>',
        "hero.lede": "Fenixd is a harness-neutral automated software development loop framework, supporting Claude Code, DSH and other harnesses. It distills natural-language requirements into SPECs and runs a controlled loop, <strong>implement → verify independently → bounce back and fix</strong>, delivering code that is implemented, verified and shippable. The only human gate is the final approval to push.",
        "hero.cta1": "What is Fenixd", "hero.cta2": "Get Started",
        "chat.title": "Fenixd, conversational delivery",
        "chat.u1": "Add email login to the user center, with password login disableable",
        "chat.a1": "Intent clarified, full SPEC generated: proposal · design · specs · tasks. Recommended mode: full.",
        "chat.a2": "After review, the daemon picks it up automatically and implements all 14 tasks in an isolated worktree; the loop-verified suite then passes all 6 scenarios with zero LLM calls.",
        "chat.a3": "The state is done; automated delivery needs one last step, your approval to push, the single human gate in the whole loop.",
        "chat.k1": "/fenix-new", "chat.k2": "Type your next requirement…", "chat.send": "Send",
        "stats.title": "Fenixd in numbers", "stats.lede": "Fenixd drives its own evolution, these numbers come from its own repository (all figures on this prototype page are sample data).",
        "cap.eyebrow": "WHAT PROBLEM FENIXD SOLVES", "cap.title": "The problem Fenixd solves",
        "cap.lede": "AI made code ten times faster to write, and software entropy ten times faster to accumulate. When generation outpaces comprehension and verification, chaos compounds: new features ship relentlessly while old ones quietly break. Fenixd fights back with four classes of mechanisms, SPEC-driven specs, verification loops, quality gates and knowledge distillation, upgrading constraints from spoken guidelines to machine-enforced hard gates.",
        "q.eyebrow": "QUICKSTART", "q.title": "Three steps to spin up the loop",
        "q.lede": "No database, no service cluster, all state lives in plain files inside your repository.",
        "ev.lede": "Code is delivered and verified automatically by the daemon; every SPEC transition and every agent action is visible live on the Dashboard.",
        "ev.c1": "SPEC ledger: from one sentence to approved push, states at a glance",
        "ev.c2": "Command Center: instances, success rate and daily activity of 12 agent classes",
        "ev.c3": "Activity stream: who read what, changed what, and why, at any time",
        "g.eyebrow": "DOCS PREVIEW", "g.title": "From quick start to deep governance",
        "g.lede": "12 topics + 3 handbooks, kept in sync with the Dashboard's Help menu.",
        "dog.title": "Fenixd is developed by Fenixd",
        "dog.lede": "Its own repository has pushed 500+ SPECs fully automatically (implement → verify → bounce back → merge), the most direct field validation of the framework, including the site you are looking at.",
        "dog.cta1": "See how the loop works", "dog.cta2": "Visit GitHub",
    })
    i18n = {"zh": zh, "en": en}

    cap_cards = [
        ("spec",   "cap.1.t", "cap.1.d", "ember"),
        ("loop",   "cap.2.t", "cap.2.d", ""),
        ("shield", "cap.3.t", "cap.3.d", "green"),
        ("book",   "cap.4.t", "cap.4.d", ""),
        ("grid",   "cap.5.t", "cap.5.d", ""),
        ("box",    "cap.6.t", "cap.6.d", ""),
        ("wrench", "cap.7.t", "cap.7.d", ""),
        ("monitor","cap.8.t", "cap.8.d", ""),
    ]
    caps_html = "".join(
        f'''<article class="card" data-proto-id="home-cap-card-{i+1}">
  <div class="card-head"><div class="card-ic">{icon(ic)}</div><h3 data-i18n="{k}">…</h3></div>
  <p data-i18n="{d}">…</p>
  <a class="card-link" href="capabilities.html" data-i18n="cap.more">了解详情 {icon("arrow","ic")}</a>
</article>'''
        for i, (ic, k, d, _) in enumerate(cap_cards))

    doc_cards = [
        ("01", "g.1.t", "g.1.d"), ("02", "g.2.t", "g.2.d"),
        ("03", "g.3.t", "g.3.d"), ("04", "g.4.t", "g.4.d"),
    ]
    docs_html = "".join(
        f'''<a class="doc-card" href="docs.html" data-proto-id="home-doc-card-{n}">
  <span class="no mono">{n} · HELP</span>
  <span class="tt" data-i18n="{t}">…</span>
  <span class="ds" data-i18n="{d}">…</span>
</a>'''
        for n, t, d in doc_cards)

    content = f"""
<section class="hero" data-proto-id="home-hero">
  <div class="wrap hero-grid">
    <div data-proto-id="home-hero-copy">
      <p class="eyebrow" data-i18n="hero.eyebrow">FENIX AI-NATIVE SDLC DEVELOPMENT</p>
      <h1 data-i18n="hero.h1">…</h1>
      <p class="lede" data-i18n="hero.lede">…</p>
      <div class="hero-ctas" data-proto-id="home-hero-ctas">
        <a class="btn btn-ghost btn-lg" href="why.html" data-i18n="hero.cta1">什么是 Fenixd</a>
        <a class="btn btn-primary btn-lg" href="#quickstart" data-i18n="hero.cta2">快速开始 {icon("arrow")}</a>
      </div>
    </div>
    <div class="chat" data-proto-id="home-hero-chat">
      <div class="chat-head"><span class="chat-logo"><img src="logo-64.png" alt=""></span>
        <span class="chat-title" data-i18n="chat.title">…</span></div>
      <div class="chat-body">
        <div class="bubble user" data-proto-id="home-chat-bubble-user"><span data-i18n="chat.u1">给用户中心加邮箱登录，要能禁用密码登录</span></div>
        <div class="bubble agent" data-proto-id="home-chat-bubble-agent">
          <span data-i18n="chat.a1">已澄清意图，生成完整 SPEC。</span>
          <span class="ctx-cards" data-proto-id="home-chat-context">
            <span class="ctx">SPEC ✓</span><span class="ctx">review ✓</span><span class="ctx">verify 6/6 ✓</span><span class="ctx">14 tasks</span>
          </span>
          <span data-i18n="chat.a2">评审通过 → daemon 拾取 → 独立 worktree 实现 14 个任务 → 零 LLM 验证 6 个场景全部通过。</span>
          <span data-i18n="chat.a3">done：等你审批推送（唯一人工门禁）。</span>
          <span class="typing" data-proto-id="home-chat-typing" aria-hidden="true"><i></i><i></i><i></i></span>
        </div>
      </div>
      <div class="chat-input" data-proto-id="home-chat-input">
        <div class="chat-field">
          <input type="text" placeholder=" " aria-label="需求输入（示例）">
          <span class="input-hint"><span class="skill-tag mono" data-i18n="chat.k1">/fenix-new</span><span data-i18n="chat.k2"> 说出你的下一个需求…</span></span>
        </div>
        <button type="button" class="chat-send"><span data-i18n="chat.send">发送</span>{icon("send")}</button>
      </div>
    </div>
  </div>
</section>

<section class="section" data-proto-id="home-capabilities">
  <div class="wrap">
    <p class="eyebrow" data-i18n="cap.eyebrow">WHAT FENIXD CAN DO</p>
    <h2 class="sec-title" data-i18n="cap.title">…</h2>
    <p class="sec-lede" style="max-width:none" data-i18n="cap.lede">…</p>
    <div class="grid-4" data-proto-id="home-cap-grid">
{caps_html}
    </div>
  </div>
</section>

<section class="section" id="quickstart" data-proto-id="home-quickstart">
  <div class="wrap">
    <p class="eyebrow" data-i18n="q.eyebrow">QUICKSTART</p>
    <h2 class="sec-title" data-i18n="q.title">…</h2>
    <p class="sec-lede" data-i18n="q.lede">…</p>
    <div class="grid-3" data-proto-id="home-quickstart-steps">
      <article class="card" data-proto-id="home-q-step-1">
        <div class="card-head"><div class="card-ic">{icon("terminal")}</div><h3 data-i18n="q.s1.t">…</h3></div>
        <p data-i18n="q.s1.d">…</p>
        <div class="term-body mono" style="border:1px solid var(--line);border-radius:8px;background:var(--term-bg);padding:10px 14px"><span class="t-p">❯</span> <span class="t-c">https://dev.icyfenix.cn/install.md</span><br><span class="t-o" data-i18n="q.s1.code">按手册安装 Fenixd 与插件</span></div>
      </article>
      <article class="card" data-proto-id="home-q-step-2">
        <div class="card-head"><div class="card-ic">{icon("spec")}</div><h3 data-i18n="q.s2.t">…</h3></div>
        <p data-i18n="q.s2.d">…</p>
        <div class="term-body mono" style="border:1px solid var(--line);border-radius:8px;background:var(--term-bg);padding:10px 14px"><span class="t-p">❯</span> <span class="t-c" style="color:var(--ember)">/fenix-new</span> <span class="t-o" data-i18n="q.s2.code">"一句话需求"</span></div>
      </article>
      <article class="card" data-proto-id="home-q-step-3">
        <div class="card-head"><div class="card-ic">{icon("rocket")}</div><h3 data-i18n="q.s3.t">…</h3></div>
        <p data-i18n="q.s3.d">…</p>
        <div class="term-body mono" style="border:1px solid var(--line);border-radius:8px;background:var(--term-bg);padding:10px 14px"><span class="t-ok">✓ done</span> <span class="t-dim" data-i18n="q.s3.code">→ /fenix-approve 审批推送</span></div>
      </article>
    </div>
    <p class="sec-lede" style="max-width:none;margin-top:56px" data-i18n="ev.lede">…</p>
    <div class="grid-3" data-proto-id="home-evidence">
      <figure class="card-shot" data-proto-id="home-ev-shot-1">
        <img src="assets/dash-project-specs.png" alt="">
        <figcaption data-i18n="ev.c1">…</figcaption>
      </figure>
      <figure class="card-shot" data-proto-id="home-ev-shot-2">
        <img src="assets/dash-command.png" alt="">
        <figcaption data-i18n="ev.c2">…</figcaption>
      </figure>
      <figure class="card-shot" data-proto-id="home-ev-shot-3">
        <img src="assets/dash-activities.png" alt="">
        <figcaption data-i18n="ev.c3">…</figcaption>
      </figure>
    </div>
  </div>
</section>

<section class="section" data-proto-id="home-guides">
  <div class="wrap">
    <p class="eyebrow" data-i18n="g.eyebrow">DOCS PREVIEW</p>
    <h2 class="sec-title" data-i18n="g.title">…</h2>
    <p class="sec-lede" data-i18n="g.lede">…</p>
    <div class="grid-4" data-proto-id="home-doc-grid">
{docs_html}
    </div>
  </div>
</section>

<section class="section" data-proto-id="home-stats">
  <div class="wrap">
    <h2 class="sec-title" data-i18n="stats.title">…</h2>
    <p class="sec-lede" data-i18n="stats.lede">…</p>
    <div class="stats" data-proto-id="home-stats-grid">
      <div class="stat"><div class="v num">500+</div><div class="k" data-i18n="stat.1">…</div></div>
      <div class="stat"><div class="v num">12</div><div class="k" data-i18n="stat.2">…</div></div>
      <div class="stat"><div class="v num">3</div><div class="k" data-i18n="stat.3">…</div></div>
      <div class="stat"><div class="v num">11</div><div class="k" data-i18n="stat.4">…</div></div>
      <div class="stat"><div class="v num">0</div><div class="k" data-i18n="stat.5">…</div></div>
    </div>
    <div class="cta-band" data-proto-id="home-dogfood-band">
      <h2 data-i18n="dog.title">…</h2>
      <p data-i18n="dog.lede">…</p>
      <div class="hero-ctas">
        <a class="btn btn-ghost" href="why.html" data-i18n="dog.cta1">看看它是怎么运转的</a>
        <a class="btn btn-primary" href="https://github.com/fenixsoft/fenixd" data-i18n="dog.cta2">访问 GitHub{icon("github")}</a>
      </div>
    </div>
  </div>
</section>

"""
    zh.update({
        "cap.more": "了解详情 ", "stat.1": "个 SPEC 全自动推进（Fenixd 自身仓库）",
        "stat.2": "类 Agent 运行时角色", "stat.3": "步零信任验证流水线",
        "stat.4": "态显式状态机治理全程", "stat.5": "数据库依赖 · 文件即状态",
        "cap.1.t": "SPEC 驱动", "cap.1.d": "模糊的口头意图沉淀为结构化 SPEC（提案 / 设计 / 规格 / 任务），架构意图不再漂在聊天记录里，人与 AI 锚定同一份可审查契约。",
        "cap.2.t": "循环验证", "cap.2.d": "实现 → 独立验证 → 打回修复的受控闭环，预算与熔断约束轮次。偏差在环内被拉回，而不是跨提交累积成「代理熵」。",
        "cap.3.t": "质量门禁", "cap.3.d": "零 LLM 验证引擎逐断言执行（web / api / cli），二元裁决「通过 / 不通过」。不依赖模型自觉，把架构违规挡在合并之前。",
        "cap.4.t": "知识蒸馏", "cap.4.d": "每个 SPEC 的验收断言与架构决策回沉为仓库知识，规则库随每个迭代增强，专家经验从人脑与聊天记录蒸馏为机器可执行的约束。",
        "cap.5.t": "全局状态机", "cap.5.d": "11 态生命周期只允许合法转移。代理熵是跨提交的系统性漂移，恰好需要全局账本让它显形：任何时刻精确回答「走到哪、卡在哪」。",
        "cap.6.t": "隔离 Worktree", "cap.6.d": "每次实现跑在独立 git worktree 与分支，merge-back 冲突自愈，失控的变更永远污染不了主干。",
        "cap.7.t": "自愈熔断", "cap.7.d": "Administrator / Arbiter 自愈链自动处置困境；无法自愈时明确停靠 blocked 等人裁决，专业知识保留在循环之内。",
        "cap.8.t": "实时 Dashboard", "cap.8.d": "跨项目聚合每个 SPEC 的实时流转、日志与验证产物。熵增不可怕，不可见才可怕。",
        "q.s1.t": "① 接入 Fenixd", "q.s1.d": "把安装手册的地址交给 harness（Claude Code / dsh web），agent 读取后按说明完成 Fenixd 框架与 dsh 插件的装配。",
        "q.s1.code": "按手册安装 Fenixd 与插件",
        "q.s2.t": "② 一句话立项", "q.s2.d": "/fenix-new 是 harness 中的 skill：在对话框输入它（而非 bash 终端），说出想法即完成立项。",
        "q.s2.code": "\"一句话需求\"", "q.s3.code": "→ /fenix-approve 审批推送",
        "q.s3.t": "③ 等代码交付", "q.s3.d": "daemon 自动拾取 → 实现 → 验证 → done，你在唯一人工门禁处审批推送。",
        "g.1.t": "快速上手", "g.1.d": "从零到交付的端到端流程",
        "g.2.t": "核心概念与架构", "g.2.d": "闭环原理、12 类 Agent、执行模式",
        "g.3.t": "生命周期与状态机", "g.3.d": "11 状态全景、评审门禁、打回修复循环",
        "g.4.t": "CLI 操作手册", "g.4.d": "/fenix-* skill 逐个详解",
        "dog.cta2": "访问 GitHub",
    })
    en.update({
        "cap.more": "Learn more ",
        "stat.1": "SPECs fully auto-driven (Fenixd's own repo)",
        "stat.2": "runtime agent roles", "stat.3": "-step zero-trust verification pipeline",
        "stat.4": "explicit lifecycle states", "stat.5": "database · state as plain files",
        "cap.1.t": "SPEC-Driven", "cap.1.d": "Vague spoken intent distills into a structured SPEC (proposal / design / specs / tasks), architecture intent stops drifting in chat logs; humans and AI anchor on one reviewable contract.",
        "cap.2.t": "Verification Loop", "cap.2.d": "Implement → independent verify → bounce-back, bounded by budgets and breakers. Deviation gets pulled back inside the loop instead of accumulating across commits as agentic entropy.",
        "cap.3.t": "Quality Gates", "cap.3.d": "A zero-LLM engine executes assertions one by one (web / api / cli) and rules pass or fail, no reliance on model goodwill; violations are blocked before merge.",
        "cap.4.t": "Knowledge Distillation", "cap.4.d": "Acceptance assertions and architecture decisions sink back into repo knowledge; the rulebook grows with every iteration, expert experience distilled into machine-executable constraints.",
        "cap.5.t": "Global State Machine", "cap.5.d": "11 states, legal transitions only. Agentic entropy is systemic drift across commits, exactly what a global ledger exposes: where every SPEC is, and why, at any moment.",
        "cap.6.t": "Isolated Worktrees", "cap.6.d": "Every implementation runs in its own git worktree and branch, with merge-back self-healing, a runaway change can never pollute the trunk.",
        "cap.7.t": "Self-Healing", "cap.7.d": "Administrator / Arbiter chains handle dead ends automatically; otherwise the SPEC parks visibly at blocked awaiting human ruling, expertise stays inside the loop.",
        "cap.8.t": "Live Dashboard", "cap.8.d": "Every SPEC's live transitions, logs and verification artifacts, aggregated across projects. Entropy is not the enemy; invisible entropy is.",
        "q.s1.t": "1 · Install Fenixd", "q.s1.d": "Hand the install guide's URL to your harness (Claude Code / dsh web); the agent reads it and sets up the fenixd framework and dsh plugins as instructed.",
        "q.s1.code": "install fenixd &amp; plugins per the guide",
        "q.s2.t": "2 · File a one-liner", "q.s2.d": "/fenix-new is a harness skill: type it in the harness chat (not a bash terminal) and state your idea to start a SPEC.",
        "q.s2.code": "\"one-liner requirement\"", "q.s3.code": "→ /fenix-approve review &amp; push",
        "q.s3.t": "3 · Wait for code", "q.s3.d": "The daemon picks it up → implements → verifies → done; you approve the push at the single human gate.",
        "g.1.t": "Quick Start", "g.1.d": "End-to-end flow from zero to delivery",
        "g.2.t": "Concepts &amp; Architecture", "g.2.d": "Loop principles, 12 agent roles, execution modes",
        "g.3.t": "Lifecycle &amp; State Machine", "g.3.d": "All 11 states, review gates, bounce-back loops",
        "g.4.t": "CLI Handbook", "g.4.d": "Every /fenix-* skill explained",
        "dog.cta2": "Visit GitHub",
    })
    return shell("home", "Fenixd · 官网首页（原型）", "index", content,
                 {"zh": zh, "en": en})

# ============================================================ 页面 2：why.html
def page_why():
    zh = merge_common({
        "title": "为什么是 Fenixd · Fenixd",
        "hero.eyebrow": "WHY FENIXD", "hero.h1": "为什么是 <span class=\"grad-text\">Fenixd</span>",
        "hero.lede": "AI 把写代码变快了十倍，也让软件的混乱积累快了十倍。当生成速度超过人类理解与验证的速度，项目就会在表面的繁荣中失控，这就是 AI 时代的软件熵增。Fenixd 是一台对抗熵增的循环机器，让每一行交付的代码都带着证据。",
        "whv.1.t": "SPEC 锚定意图", "whv.1.d": "一句话需求沉淀为可评审的契约",
        "whv.2.t": "循环拉回漂移", "whv.2.d": "不顺利被建模为正常路径",
        "whv.3.t": "门禁拦截违规", "whv.3.d": "确定性检查零 LLM 参与把关",
        "whv.4.t": "蒸馏沉淀约束", "whv.4.d": "经验回沉为机器可执行的规则",
        "story.eyebrow": "A REAL COLLAPSE", "story.title": "先讲一个真实的故事",
        "story.p1": "2025 年，一位巴西工程师做了一个实验：把开发完全交给 AI 代理。一个月里他写下约 40 万行代码、发布 150 个功能，前两周势如破竹，这是 AI 编码最迷人的样子。",
        "story.p2": "随后崩塌开始了：每个新功能平均破坏三个旧功能，修复速度再也追不上破坏速度，几小时的活变成几天。他最终公开承认项目失控，并把这段经历写成了广为流传的复盘。",
        "story.p3": "这不是孤例，行业级数据正在指向同一个方向：",
        "story.d1.v": "-7.2%", "story.d1.k": "交付稳定性（DORA 2024：AI 采用率每 +25%）",
        "story.d2.v": "8%→18%", "story.d2.k": "复制粘贴代码占比 2021→2025（GitClear，2.11 亿行变更）",
        "story.d3.v": "+154%", "story.d3.k": "PR 体积膨胀（Faros AI，万名开发者样本）",
        "story.d4.v": "+91%", "story.d4.k": "审查耗时，人工逐行审查已不可能（Faros AI）",
        "story.note": "数据来源：DORA 2024 报告 · GitClear 2025（2.11 亿行变更分析）· Faros AI 2025（10,000 名开发者样本）",
        "pain.eyebrow": "THE ENTROPY LANDSCAPE", "pain.title": "AI 编码的六个失控点",
        "pain.lede": "快只是开始。当生成速度超过理解与验证的速度，失控会沿着这六条路径蔓延。<br><span style=\"font-size:13.5px;color:var(--text-3)\">速度幻觉 · 代理债务 · 漂移不可见 · 验证缺位 · 知识流失 · 反馈迟滞</span><br><strong>Fenixd 的回答：</strong>对抗熵增靠机制，不靠自觉。SPEC 驱动锚定意图，循环验证拉回漂移，质量门禁确定性拦截，知识蒸馏让约束越用越强。",
        "pain.1.t": "速度幻觉，先快后崩",
        "pain.1.d": "前两周势如破竹，随后每个新功能平均破坏三个旧功能，速度断崖式下跌。熵增不是缺陷，而是成长中系统的必然属性，AI 只是把时间尺度压缩了十倍。",
        "pain.2.t": "瓶颈从「写」转移到「懂」",
        "pain.2.d": "代码产出快了十倍，人的理解速度没有变。代码库很快变成谁也不敢乱动的黑盒，「写它的是 AI，能解释它的也只有 AI」。",
        "pain.3.t": "审查瓶颈，人工失守",
        "pain.3.d": "PR 体积膨胀 154%、审查耗时上涨 91%，人工逐行审查在规模化生成面前彻底失效，资深工程师被 PR 淹没，把关形同虚设。",
        "pain.4.t": "修一个，带三个",
        "pain.4.d": "出 Bug 只能继续让 AI 修，修一个带出新的。有客服 Agent 系统上线后结构混乱到连开发自己都解释不清内部逻辑，陷入「AI 修 AI」的循环。",
        "pain.5.t": "代理熵，漂移不可见",
        "pain.5.d": "模型持续生成「局部正确」的代码，架构意图却在跨提交漂移。diff 式审查只看局部变更，功能测试通过反而掩盖系统性退化。",
        "pain.6.t": "只写代码，重写胜过修复",
        "pain.6.d": "AI 代码过于密集难以阅读，沦为「只写（write-only）」，连作者也无法完全理解；调试不如丢弃重写，意图与实现彻底脱钩。",
        "answer.strip": "<strong>Fenixd 的回答：</strong>对抗熵增靠机制，不靠自觉，SPEC 驱动锚定意图，循环验证拉回漂移，质量门禁确定性拦截，知识蒸馏让约束越用越强。",
        "pillar.eyebrow": "FOUR MECHANISMS", "pillar.title": "对抗熵增的四类机制",
        "pillar.lede": "熵增的修复没有单点方案，Fenixd 把四层手段工程化为四个相互咬合的机制。",
        "map.eyebrow": "THE ANSWER MAP", "map.title": "逐一化解失控点",
        "map.lede": "每一个失控点都对应 Fenixd 的一项机制，不是提示词技巧，而是机器执行的工程约束。",
        "map.h1": "失控点", "map.h2": "Fenixd 的对策",
        "map.1.p": "速度幻觉，先快后崩", "map.1.d": "<strong>SPEC 驱动锚定意图</strong>，每个 SPEC 携带明确验收标准，生成快≠交付快，交付以断言全部通过为准。",
        "map.2.p": "瓶颈从写转移到懂", "map.2.d": "<strong>知识蒸馏留档</strong>，架构决策、接口契约、验收场景全部入库可检索：人读 SPEC，不必逐行读代码。",
        "map.3.p": "审查瓶颈，人工失守", "map.3.d": "<strong>零 LLM 验证引擎</strong>，机械正确性交给确定性断言（web/api/cli），人只审意图与最终批准：把关从「逐行读」变为「审契约」。",
        "map.4.p": "修一个，带三个", "map.4.d": "<strong>循环验证全量回归</strong>，每次修改跑全量验收断言，改坏即打回，永不进主干。",
        "map.5.p": "代理熵，漂移不可见", "map.5.d": "<strong>全局状态机 + 确定性门禁</strong>，11 态生命周期让每一步漂移可见、可审计，非法转移直接拒绝。",
        "map.6.p": "只写代码，重写胜过修复", "map.6.d": "<strong>SPEC 即行为文档</strong>，测试先于实现定义行为：代码可丢弃、契约长存，重写是安全的，因为行为有锚。",
        "pillar.1.t": "SPEC 驱动 · 锚定意图",
        "pillar.1.d": "在 AI 动手之前，把模糊意图沉淀为结构化 SPEC，提案、设计、需求规格与任务清单。它是全框架的通用语言：范围、接口与验收标准全部锚定在这份契约上，意图不再随对话漂移。",
        "pillar.1.b0": "提案", "pillar.1.b1": "设计", "pillar.1.b2": "需求规格", "pillar.1.b3": "任务清单",
        "pillar.2.t": "循环验证 · 拉回漂移",
        "pillar.2.d": "「实现 → 独立验证 → 打回修复」的受控闭环：真实浏览器级测试代替主观自评，预算与熔断约束轮次。偏差在环内被拉回，而非跨提交累积成代理熵。",
        "pillar.2.b0": "受控闭环", "pillar.2.b1": "预算熔断", "pillar.2.b2": "真实测试",
        "pillar.3.t": "质量门禁 · 确定性闸门",
        "pillar.3.d": "零 LLM 验证引擎逐断言执行 web / api / cli 断言，二元裁决「通过 / 不通过」。在概率性的模型约束之上再叠一层确定性硬闸门，架构违规不靠「提醒」，靠「拦截」。",
        "pillar.3.b0": "零 LLM", "pillar.3.b1": "web · api · cli", "pillar.3.b2": "二元裁决",
        "pillar.4.t": "知识蒸馏 · 约束增强",
        "pillar.4.d": "每个 SPEC 的验收断言与架构决策回沉为仓库知识与规则库，约束随每个迭代增强；专家从「全程盯梢」转向「构建约束」，经验蒸馏为机器可执行的资产。",
        "pillar.4.b0": "断言入库", "pillar.4.b1": "规则增强", "pillar.4.b2": "专家在环",
        "loop.eyebrow": "THE LOOP", "loop.title": "一个 SPEC 的受控一生",
        "loop.lede": "每一次转移都必须符合状态机的合法转移表，「不顺利」被建模为正常路径。漂移不会累积，因为每一圈都会把它拉回来。",
        "loop.n1.t": "需求", "loop.n1.d": "/fenix-new", "loop.n2.t": "SPEC", "loop.n2.d": "proposal→tasks",
        "loop.n3.t": "方案评审", "loop.n3.d": "single-pass review", "loop.n4.t": "实现", "loop.n4.d": "isolated worktree",
        "loop.n5.t": "独立验证", "loop.n5.d": "zero-LLM", "loop.n6.t": "完成", "loop.n6.d": "done",
        "loop.n7.t": "审批推送", "loop.n7.d": "human gate",
        "loop.back": "验证不过 → 打回修复（预算与熔断约束循环次数）",
        "cmp.eyebrow": "COMPARISON", "cmp.title": "与「人工 Prompt 流」的差别",
        "cmp.lede": "同样的模型，不同的工作组织方式，交付质量天差地别。",
        "cmp.h1": "维度", "cmp.h2": "人工 Prompt 流", "cmp.h3": "Fenixd 闭环",
        "cmp.r1.k": "架构意图", "cmp.r1.a": "口头约定，边做边漂移", "cmp.r1.b": "SPEC 契约锚定，单一真源",
        "cmp.r2.k": "约束方式", "cmp.r2.a": "概率性：提示词与自觉", "cmp.r2.b": "确定性：零 LLM 门禁 + 循环拉回",
        "cmp.r3.k": "漂移可见性", "cmp.r3.a": "散落聊天记录，事后才炸", "cmp.r3.b": "11 态状态机 + Dashboard 实时显形",
        "cmp.r4.k": "失败处理", "cmp.r4.a": "重新描述、重新粘贴、祈祷", "cmp.r4.b": "打回修复循环 + 预算熔断 + 停靠 blocked",
        "cmp.r5.k": "知识沉淀", "cmp.r5.a": "经验留在人脑与聊天记录", "cmp.r5.b": "断言与决策每次迭代蒸馏进仓库",
        "ev.eyebrow": "EVIDENCE", "ev.title": "最直接的验证：它开发它自己",
        "ev.lede": "Fenixd 自身的演进完全由 Fenixd 驱动，本仓库 500+ 个 SPEC 全自动推进，包括功能开发、缺陷修复与文档演进。",
        "ev.1.v": "500+", "ev.1.k": "SPEC 全自动推进", "ev.2.v": "2×", "ev.2.k": "周期车道：代码审查 + 缺陷修复",
        "ev.3.v": "1", "ev.3.k": "个人工门禁：审批推送", "ev.4.v": "24/7", "ev.4.k": "daemon 常驻调度",
        "ev.note": "（数字为原型示例数据）",
        "cta.t": "把你的下一次「口述需求」交给循环",
        "cta.d": "五分钟装好 daemon，第一句话就是你的第一个 SPEC。",
        "cta.b1": "快速开始", "cta.b2": "先读文档",
    })
    en = merge_common_en({
        "title": "Why Fenixd · Fenixd",
        "hero.eyebrow": "WHY FENIXD", "hero.h1": 'Why <span class="grad-text">Fenixd</span>',
        "hero.lede": "AI made writing code ten times faster, and made software chaos accumulate ten times faster, too. When generation outpaces human comprehension and verification, projects spiral out of control amid apparent prosperity. That is software entropy in the AI era. Fenixd is a loop machine built to fight it, and every delivered line carries evidence.",
        "whv.1.t": "SPEC anchors intent", "whv.1.d": "One sentence becomes a reviewable contract",
        "whv.2.t": "Loops pull back drift", "whv.2.d": "Failure is modeled as a normal path",
        "whv.3.t": "Gates block violations", "whv.3.d": "Deterministic checks, zero LLM in the loop",
        "whv.4.t": "Distillation compounds", "whv.4.d": "Experience settles into executable rules",
        "story.eyebrow": "A REAL COLLAPSE", "story.title": "First, a true story",
        "story.p1": "In 2025, a Brazilian engineer ran an experiment: hand development entirely to AI agents. In one month he produced about 400,000 lines of code and shipped 150 features. The first weeks felt unstoppable, AI coding at its most seductive.",
        "story.p2": "Then the collapse began: every new feature broke three old ones on average. Fixes could never catch up with breakage; hours of work turned into days. He eventually admitted the project was out of control and published a now-famous post-mortem.",
        "story.p3": "This is not an outlier, industry-wide data points the same way:",
        "story.d1.v": "-7.2%", "story.d1.k": "Delivery stability per +25% AI adoption (DORA 2024)",
        "story.d2.v": "8%→18%", "story.d2.k": "Copy-pasted code share 2021→2025 (GitClear, 211M changed lines)",
        "story.d3.v": "+154%", "story.d3.k": "PR size inflation (Faros AI, 10K-developer sample)",
        "story.d4.v": "+91%", "story.d4.k": "Review time, line-by-line review has failed (Faros AI)",
        "story.note": "Sources: DORA 2024 report · GitClear 2025 (211M changed lines) · Faros AI 2025 (10,000-developer sample)",
        "pain.eyebrow": "THE ENTROPY LANDSCAPE", "pain.title": "Six ways AI coding spins out of control",
        "pain.lede": "Speed is just the beginning. When generation outpaces comprehension and verification, failure spreads along six paths.<br><span style=\"font-size:13.5px;color:var(--text-3)\">Speed illusion · Agent debt · Invisible drift · Missing verification · Knowledge loss · Slow feedback</span><br><strong>Fenixd's answer:</strong> fight entropy with mechanisms, not goodwill. SPEC-driven anchoring, verification loops pulling drift back, deterministic quality gates, and knowledge distillation that makes constraints compound.",
        "pain.1.t": "The speed illusion: fast first, collapse later",
        "pain.1.d": "The first weeks feel unstoppable; then every new feature breaks three old ones on average and velocity falls off a cliff. Entropy is not a defect but a property of growing systems, AI just compressed the time scale tenfold.",
        "pain.2.t": "The bottleneck moves from writing to understanding",
        "pain.2.d": "Code now ships ten times faster, but human comprehension didn't speed up. The codebase quickly becomes a black box nobody dares to touch, \"AI wrote it, and only AI can explain it\".",
        "pain.3.t": "Review breaks down at scale",
        "pain.3.d": "PRs grow 154% bigger and review time rises 91%, line-by-line human review simply fails at scale. Senior engineers drown in pull requests while quality gates become a formality.",
        "pain.4.t": "Fix one, break three",
        "pain.4.d": "When bugs appear, the only answer is \"let AI fix it\", and each fix breeds new bugs. A customer-service agent system shipped so tangled that even its own developers couldn't explain its logic.",
        "pain.5.t": "Agentic entropy: invisible drift",
        "pain.5.d": "The model keeps producing \"locally correct\" code while architectural intent drifts across commits. Diff-based review only sees local changes; passing feature tests mask systemic degradation.",
        "pain.6.t": "Write-only code: rewriting beats fixing",
        "pain.6.d": "AI code is too dense to read, \"write-only\", even its author can't fully understand it. Debugging loses to throwaway rewrites, and intent decouples from implementation.",
        "answer.strip": "<strong>Fenixd's answer:</strong> fight entropy with mechanisms, not goodwill, SPEC-driven anchoring, verification loops pulling drift back, deterministic quality gates, and knowledge distillation that makes constraints compound.",
        "pillar.eyebrow": "FOUR MECHANISMS", "pillar.title": "Four mechanisms against entropy",
        "pillar.lede": "There is no single-point fix for entropy, Fenixd engineers four layers into four interlocking mechanisms.",
        "map.eyebrow": "THE ANSWER MAP", "map.title": "Resolving failure modes one by one",
        "map.lede": "Every failure path maps to a Fenixd mechanism, not prompt tricks, but machine-enforced engineering constraints.",
        "map.h1": "Failure path", "map.h2": "Fenixd's answer",
        "map.1.p": "The speed illusion", "map.1.d": "<strong>SPEC-driven intent anchoring</strong>, every SPEC carries explicit acceptance criteria; shipping fast ≠ delivering fast, and delivery means all assertions pass.",
        "map.2.p": "Understanding becomes the bottleneck", "map.2.d": "<strong>Knowledge distillation</strong>, architectural decisions, API contracts and acceptance scenarios are banked and searchable; humans read SPECs, not every line of code.",
        "map.3.p": "Review breaks down", "map.3.d": "<strong>Zero-LLM verification engine</strong>, mechanical correctness goes to deterministic assertions (web/api/cli); humans review intent and give final approval. Gatekeeping shifts from reading lines to reviewing contracts.",
        "map.4.p": "Fix one, break three", "map.4.d": "<strong>Full-regression verification loops</strong>, every change runs the entire assertion suite; breakage bounces back and never lands on main.",
        "map.5.p": "Invisible agentic drift", "map.5.d": "<strong>Global state machine + deterministic gates</strong>, an 11-state lifecycle makes every step visible and auditable; illegal transitions are rejected outright.",
        "map.6.p": "Write-only code", "map.6.d": "<strong>SPECs as behavioral documentation</strong>, tests define behavior before implementation; code is disposable, contracts persist. Rewrites are safe because behavior has an anchor.",
        "pillar.1.t": "SPEC-Driven · Anchor Intent",
        "pillar.1.d": "Before the AI writes code, vague intent distills into a structured SPEC, proposal, design, requirement specs and a task list. It is the framework's common language: scope, interfaces and acceptance criteria all anchor to this contract, so intent stops drifting with the conversation.",
        "pillar.1.b0": "Proposal", "pillar.1.b1": "Design", "pillar.1.b2": "Specs", "pillar.1.b3": "Tasks",
        "pillar.2.t": "Verification Loop · Pull Drift Back",
        "pillar.2.d": "Implement → verify independently → bounce back, as one controlled loop: browser-grade tests replace self-assessment; budgets and breakers bound the iterations. Deviation is pulled back inside the loop instead of accumulating across commits.",
        "pillar.2.b0": "Controlled loop", "pillar.2.b1": "Budget breakers", "pillar.2.b2": "Real tests",
        "pillar.3.t": "Quality Gates · Deterministic Blocking",
        "pillar.3.d": "A zero-LLM engine executes web / api / cli assertions one by one and rules pass or fail. On top of probabilistic model constraints sits a deterministic hard gate, violations are not \"reminded\", they are \"blocked\".",
        "pillar.3.b0": "Zero-LLM", "pillar.3.b1": "web · api · cli", "pillar.3.b2": "Pass or fail",
        "pillar.4.t": "Knowledge Distillation · Compounding Constraints",
        "pillar.4.d": "Acceptance assertions and architecture decisions sink back into repo knowledge; the rulebook grows with every iteration. Experts shift from \"watching every step\" to \"building constraints\", distilling experience into machine-executable assets.",
        "pillar.4.b0": "Assertions banked", "pillar.4.b1": "Rules compound", "pillar.4.b2": "Experts in loop",
        "loop.eyebrow": "THE LOOP", "loop.title": "The controlled life of a SPEC",
        "loop.lede": "Every transition must be legal in the state machine, \"going wrong\" is a modeled normal path. Drift never accumulates, because every lap pulls it back.",
        "loop.n1.t": "Requirement", "loop.n1.d": "/fenix-new", "loop.n2.t": "SPEC", "loop.n2.d": "proposal→tasks",
        "loop.n3.t": "Review", "loop.n3.d": "single-pass review", "loop.n4.t": "Implement", "loop.n4.d": "isolated worktree",
        "loop.n5.t": "Verify", "loop.n5.d": "zero-LLM", "loop.n6.t": "Done", "loop.n6.d": "done",
        "loop.n7.t": "Approve &amp; Push", "loop.n7.d": "human gate",
        "loop.back": "verification fails → bounce back &amp; fix (budgets bound the iterations)",
        "cmp.eyebrow": "COMPARISON", "cmp.title": "Versus the manual prompt flow",
        "cmp.lede": "Same models, different organization of work, radically different delivery quality.",
        "cmp.h1": "Dimension", "cmp.h2": "Manual prompting", "cmp.h3": "Fenixd loop",
        "cmp.r1.k": "Architecture intent", "cmp.r1.a": "Verbal agreement in chat, drifting as you go", "cmp.r1.b": "SPEC contract as single source of truth",
        "cmp.r2.k": "Constraint style", "cmp.r2.a": "Probabilistic: prompts and goodwill", "cmp.r2.b": "Deterministic: zero-LLM gates + loop pull-back",
        "cmp.r3.k": "Drift visibility", "cmp.r3.a": "Buried in chat history, blows up later", "cmp.r3.b": "11-state machine + live Dashboard exposure",
        "cmp.r4.k": "Failure handling", "cmp.r4.a": "Re-explain, re-paste, pray", "cmp.r4.b": "Bounce-back loop + budget breakers + blocked parking",
        "cmp.r5.k": "Knowledge", "cmp.r5.a": "Lives in brains and chat logs", "cmp.r5.b": "Assertions and decisions distilled into the repo every iteration",
        "ev.eyebrow": "EVIDENCE", "ev.title": "The most direct validation: it develops itself",
        "ev.lede": "Fenixd's own evolution is driven entirely by Fenixd, 500+ SPECs pushed fully automatically in this repository, spanning features, bug fixes and docs.",
        "ev.1.v": "500+", "ev.1.k": "SPECs auto-driven", "ev.2.v": "2×", "ev.2.k": "background lanes: code review + fixes",
        "ev.3.v": "1", "ev.3.k": "human gate: approve to push", "ev.4.v": "24/7", "ev.4.k": "resident daemon scheduling",
        "ev.note": "(sample data for the prototype)",
        "cta.t": "Hand your next spoken requirement to the loop",
        "cta.d": "Install the daemon in five minutes; your first sentence becomes your first SPEC.",
        "cta.b1": "Get Started", "cta.b2": "Read the docs first",
    })
    i18n = {"zh": zh, "en": en}

    story_data = "".join(
        f'''<div class="stat" data-proto-id="why-story-data-{i+1}"><div class="v num" data-i18n="story.d{i+1}.v">…</div>
<div class="k" data-i18n="story.d{i+1}.k">…</div></div>'''
        for i in range(4))

    pain_cards = "".join(
        f'''<article class="card" data-proto-id="why-pain-{i+1}">
  <span class="num-badge">0{i+1} ✕</span>
  <h3 data-i18n="pain.{i+1}.t">…</h3>
  <p data-i18n="pain.{i+1}.d">…</p>
</article>''' for i in range(6))

    pillar_html = f"""
<div class="grid-4" data-proto-id="why-pillars-grid">
  <article class="card" data-proto-id="why-pillar-spec">
    <div class="card-head"><div class="card-ic">{icon("spec")}</div><h3 data-i18n="pillar.1.t">…</h3></div>
    <p data-i18n="pillar.1.d">…</p>
    <div class="tagline">
      <span class="tag ember" data-i18n="pillar.1.b0">提案</span>
      <span class="tag" data-i18n="pillar.1.b1">设计</span>
      <span class="tag" data-i18n="pillar.1.b2">需求规格</span>
      <span class="tag" data-i18n="pillar.1.b3">任务清单</span>
    </div>
  </article>
  <article class="card" data-proto-id="why-pillar-loop">
    <div class="card-head"><div class="card-ic">{icon("loop")}</div><h3 data-i18n="pillar.2.t">…</h3></div>
    <p data-i18n="pillar.2.d">…</p>
    <div class="tagline">
      <span class="tag green" data-i18n="pillar.2.b0">受控闭环</span>
      <span class="tag" data-i18n="pillar.2.b1">预算熔断</span>
      <span class="tag" data-i18n="pillar.2.b2">真实测试</span>
    </div>
  </article>
  <article class="card" data-proto-id="why-pillar-gate">
    <div class="card-head"><div class="card-ic">{icon("shield")}</div><h3 data-i18n="pillar.3.t">…</h3></div>
    <p data-i18n="pillar.3.d">…</p>
    <div class="tagline">
      <span class="tag ember" data-i18n="pillar.3.b0">零 LLM</span>
      <span class="tag" data-i18n="pillar.3.b1">web · api · cli</span>
      <span class="tag" data-i18n="pillar.3.b2">二元裁决</span>
    </div>
  </article>
  <article class="card" data-proto-id="why-pillar-distill">
    <div class="card-head"><div class="card-ic">{icon("book")}</div><h3 data-i18n="pillar.4.t">…</h3></div>
    <p data-i18n="pillar.4.d">…</p>
    <div class="tagline">
      <span class="tag ember" data-i18n="pillar.4.b0">断言入库</span>
      <span class="tag" data-i18n="pillar.4.b1">规则增强</span>
      <span class="tag" data-i18n="pillar.4.b2">专家在环</span>
    </div>
  </article>
</div>"""

    loop_nodes = [("loop.n1.t","loop.n1.d","hl"),("loop.n2.t","loop.n2.d",""),
                  ("loop.n3.t","loop.n3.d",""),("loop.n4.t","loop.n4.d","hl"),
                  ("loop.n5.t","loop.n5.d",""),("loop.n6.t","loop.n6.d",""),
                  ("loop.n7.t","loop.n7.d","gate")]
    arrows = "".join(
        f'''<div class="loop-node {c}" data-proto-id="why-loop-node-{i+1}">
  <div class="t" data-i18n="{t}">…</div><div class="d mono" data-i18n="{d}">…</div>
</div>''' + ('<div class="loop-arrow">' + icon("arrow") + '</div>' if i < len(loop_nodes)-1 else '')
        for i, (t, d, c) in enumerate(loop_nodes))

    rows = [("cmp.r1.k","cmp.r1.a","cmp.r1.b"),("cmp.r2.k","cmp.r2.a","cmp.r2.b"),
            ("cmp.r3.k","cmp.r3.a","cmp.r3.b"),("cmp.r4.k","cmp.r4.a","cmp.r4.b"),
            ("cmp.r5.k","cmp.r5.a","cmp.r5.b")]
    rows_html = "".join(
        f'''<tr data-proto-id="why-cmp-row-{i+1}">
  <td data-i18n="{k}">…</td><td data-i18n="{a}">…</td><td class="col-fenix" data-i18n="{b}">…</td>
</tr>''' for i, (k, a, b) in enumerate(rows))
    map_rows = "".join(
        f'''<tr data-proto-id="why-map-row-{i+1}">
  <td data-i18n="map.{i+1}.p">…</td><td class="col-fenix" data-i18n="map.{i+1}.d">…</td>
</tr>'''
        for i in range(6))

    stats_html = "".join(
        f'''<div class="stat" data-proto-id="why-ev-{i+1}"><div class="v num" data-i18n="ev.{i+1}.v">…</div>
<div class="k" data-i18n="ev.{i+1}.k">…</div></div>'''
        for i in range(4))

    content = f"""
<section class="hero" data-proto-id="why-hero">
  <div class="wrap hero-split">
    <div class="hero-copy">
      <p class="eyebrow" data-i18n="hero.eyebrow">WHY FENIXD</p>
      <h1 data-i18n="hero.h1">…</h1>
      <p class="lede" data-i18n="hero.lede">…</p>
    </div>
    <div class="hero-vis" data-proto-id="why-hero-vis">
      <a class="hv-card" href="#why-pillar-spec" data-proto-id="why-hero-vis-1">
        <div class="hv-head"><span class="hv-ic">{icon("lu-file-text")}</span><span class="hv-t" data-i18n="whv.1.t">SPEC 锚定意图</span></div>
        <span class="hv-d" data-i18n="whv.1.d">…</span>
      </a>
      <a class="hv-card" href="#why-pillar-loop" data-proto-id="why-hero-vis-2">
        <div class="hv-head"><span class="hv-ic">{icon("loop")}</span><span class="hv-t" data-i18n="whv.2.t">循环拉回漂移</span></div>
        <span class="hv-d" data-i18n="whv.2.d">…</span>
      </a>
      <a class="hv-card" href="#why-pillar-gate" data-proto-id="why-hero-vis-3">
        <div class="hv-head"><span class="hv-ic">{icon("lu-shield-check")}</span><span class="hv-t" data-i18n="whv.3.t">门禁拦截违规</span></div>
        <span class="hv-d" data-i18n="whv.3.d">…</span>
      </a>
      <a class="hv-card" href="#why-pillar-distill" data-proto-id="why-hero-vis-4">
        <div class="hv-head"><span class="hv-ic">{icon("book")}</span><span class="hv-t" data-i18n="whv.4.t">蒸馏沉淀约束</span></div>
        <span class="hv-d" data-i18n="whv.4.d">…</span>
      </a>
    </div>
  </div>
</section>

<section class="section" data-proto-id="why-story">
  <div class="wrap">
    <p class="eyebrow" data-i18n="story.eyebrow">A REAL COLLAPSE</p>
    <h2 class="sec-title" data-i18n="story.title">…</h2>
    <p class="sec-lede" style="max-width:none" data-i18n="story.p1">…</p>
    <p class="sec-lede" style="max-width:none;margin-top:12px" data-i18n="story.p2">…</p>
    <p style="margin-top:20px;font-weight:600;color:var(--text)" data-i18n="story.p3">…</p>
    <div class="stats" style="grid-template-columns:repeat(4,1fr);margin-top:14px" data-proto-id="why-story-data">
{story_data}
    </div>
    <p class="mono" style="color:var(--text-3);font-size:12px;margin-top:12px" data-i18n="story.note">…</p>
  </div>
</section>

<section class="section" data-proto-id="why-painpoints">
  <div class="wrap">
    <p class="eyebrow" data-i18n="pain.eyebrow">THE PROBLEM</p>
    <h2 class="sec-title" data-i18n="pain.title">…</h2>
    <p class="sec-lede" style="max-width:none" data-i18n="pain.lede">…</p>
    <div class="pain" data-proto-id="why-pain-grid">
{pain_cards}
    </div>
  </div>
</section>

<section class="section" data-proto-id="why-pillars">
  <div class="wrap">
    <p class="eyebrow" data-i18n="pillar.eyebrow">TWO IDEAS</p>
    <h2 class="sec-title" data-i18n="pillar.title">…</h2>
    <p class="sec-lede" data-i18n="pillar.lede">…</p>
{pillar_html}
  </div>
</section>

<section class="section" data-proto-id="why-mapping">
  <div class="wrap">
    <p class="eyebrow" data-i18n="map.eyebrow">THE ANSWER MAP</p>
    <h2 class="sec-title" data-i18n="map.title">…</h2>
    <p class="sec-lede" style="max-width:none" data-i18n="map.lede">…</p>
    <table class="cmp" data-proto-id="why-map-table">
      <thead><tr>
        <th data-i18n="map.h1">失控点</th>
        <th class="col-fenix" data-i18n="map.h2">Fenixd 的对策</th>
      </tr></thead>
      <tbody>
{map_rows}
      </tbody>
    </table>
  </div>
</section>

<section class="section" data-proto-id="why-loop">
  <div class="wrap">
    <p class="eyebrow" data-i18n="loop.eyebrow">THE LOOP</p>
    <h2 class="sec-title" data-i18n="loop.title">…</h2>
    <p class="sec-lede" style="max-width:none" data-i18n="loop.lede">…</p>
    <div class="loop-diagram" data-proto-id="why-loop-diagram">
{arrows}
    </div>
    <div class="loop-back" data-proto-id="why-loop-back">{icon("loop")}<span data-i18n="loop.back">…</span></div>
  </div>
</section>

<section class="section" data-proto-id="why-comparison">
  <div class="wrap">
    <p class="eyebrow" data-i18n="cmp.eyebrow">COMPARISON</p>
    <h2 class="sec-title" data-i18n="cmp.title">…</h2>
    <p class="sec-lede" data-i18n="cmp.lede">…</p>
    <table class="cmp" data-proto-id="why-cmp-table">
      <thead><tr>
        <th data-i18n="cmp.h1">维度</th>
        <th data-i18n="cmp.h2">人工 Prompt 流</th>
        <th class="col-fenix" data-i18n="cmp.h3">Fenixd 闭环</th>
      </tr></thead>
      <tbody>
{rows_html}
      </tbody>
    </table>
  </div>
</section>

<section class="section" data-proto-id="why-evidence">
  <div class="wrap">
    <p class="eyebrow" data-i18n="ev.eyebrow">EVIDENCE</p>
    <h2 class="sec-title" data-i18n="ev.title">…</h2>
    <p class="sec-lede" data-i18n="ev.lede">…</p>
    <div class="stats" style="grid-template-columns:repeat(4,1fr)" data-proto-id="why-ev-grid">
{stats_html}
    </div>
    <p class="mono" style="color:var(--text-3);font-size:12px;margin-top:14px" data-i18n="ev.note">…</p>
<div class="cta-band" style="margin-top:36px" data-proto-id="why-cta-band">
      <h2 data-i18n="cta.t">…</h2>
      <p data-i18n="cta.d">…</p>
      <div class="hero-ctas">
        <a class="btn btn-primary" href="index.html#quickstart" data-i18n="cta.b1">快速开始</a>
        <a class="btn btn-ghost" href="docs.html" data-i18n="cta.b2">先读文档</a>
      </div>
    </div>
  </div>
</section>

"""
    return shell("why", "为什么是 Fenixd（原型）", "why", content,
                 {"zh": merge_common(zh), "en": merge_common_en(en)})

# ============================================================ 页面 3：capabilities.html
def lifecycle_svg():
    """11 态状态机全景图（蛇形两行布局；参照 docs/help/03-lifecycle.md 状态全景绘制，静态 SVG 零动画）"""
    W, H = 880, 400
    NW, NH = 108, 42
    ROW1, ROW2 = 80, 310
    MAIN = [("drafted", 40, "line-strong", ROW1), ("ready", 210, "line-strong", ROW1),
            ("implementing", 380, "ember", ROW1), ("implemented", 560, "line-strong", ROW1),
            ("testing", 740, "line-strong", ROW2), ("verified", 560, "verified", ROW2),
            ("done", 380, "verified", ROW2), ("pushed", 200, "verified", ROW2)]
    SIDE = [("reviewing", 210, "link", 190), ("blocked", 380, "danger", 190),
            ("bug-found", 560, "warn", 190)]

    def node(x, y, name, stroke):
        return (f'<g data-proto-id="cap-lc-node-{name}"><rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="10" '
                f'fill="var(--card)" stroke="var(--{stroke})" stroke-width="1.5"/>'
                f'<text x="{x+NW//2}" y="{y+NH//2+4.5}" text-anchor="middle" '
                f'font-family="var(--mono)" font-size="12.5" fill="var(--text-1)">{name}</text></g>')

    def arrow(x1, y1, x2, y2, label, lx, ly, curve=None):
        if curve:
            path = f'<path d="{curve}" fill="none" stroke="var(--text-3)" stroke-width="1.4" marker-end="url(#lcA)"/>'
        else:
            path = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--text-3)" stroke-width="1.4" marker-end="url(#lcA)"/>'
        return path + (f'<text x="{lx}" y="{ly}" font-family="var(--mono)" font-size="10" '
                       f'fill="var(--text-3)" text-anchor="middle">{label}</text>' if label else '')

    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="fenixd lifecycle state machine">',
             '<defs><marker id="lcA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
             '<path d="M0,0L10,5L0,10z" fill="var(--text-3)"/></marker></defs>']
    # 起点（行1 左端） / 终点（行2 pushed 左侧）
    parts.append('<g data-proto-id="cap-lc-start"><circle cx="16" cy="101" r="5" fill="var(--ember)"/></g>')
    parts.append('<g data-proto-id="cap-lc-end"><circle cx="150" cy="331" r="10" fill="none" stroke="var(--verified)" stroke-width="1.5"/>'
                 '<circle cx="150" cy="331" r="5" fill="var(--verified)"/></g>')
    # 行1 直箭 + U 形拐弯进 testing + 行2 右→左直箭 + pushed→终点
    parts += [
        arrow(23, 101, 36, 101, None, 0, 0),
        arrow(148, 101, 206, 101, "direct", 177, 90),
        arrow(318, 101, 376, 101, "dispatch", 347, 90),
        arrow(492, 101, 556, 101, None, 0, 0),
        arrow(0, 0, 0, 0, "done", 731, 90, "M668,101 L770,101 Q794,101 794,125 L794,302"),
        arrow(736, 331, 672, 331, "verify", 704, 320),
        arrow(556, 331, 492, 331, "pass", 524, 320),
        arrow(376, 331, 312, 331, "auto", 344, 320),
        arrow(196, 331, 166, 331, "approve", 179, 358),
    ]
    # 曲线边（中间带支线）
    parts += [
        arrow(0, 0, 0, 0, "review gate", 231, 160, "M264,122 L264,186"),
        arrow(0, 0, 0, 0, "approved", 376, 182, "M322,206 C350,198 372,158 386,128"),
        arrow(0, 0, 0, 0, "rejected", 176, 176, "M214,208 C186,182 198,142 226,126"),
        arrow(0, 0, 0, 0, "unfreeze", 357, 160, "M396,186 C382,162 382,146 392,126"),
        arrow(0, 0, 0, 0, "circuit-break", 462, 160, "M430,126 C442,150 442,166 428,184"),
        arrow(0, 0, 0, 0, "retry", 350, 40, "M434,76 C398,50 300,50 266,74"),
        arrow(0, 0, 0, 0, "bug-found", 648, 162, "M614,126 L612,186"),
        arrow(0, 0, 0, 0, "fix done", 740, 254, "M668,215 C712,232 744,272 756,302"),
        arrow(0, 0, 0, 0, "fix &amp; re-dispatch", 545, 190, "M552,219 C500,212 470,172 456,132"),
    ]
    for name, x, stroke, y in MAIN + SIDE:
        parts.append(node(x, y, name, stroke))
    parts.append('</svg>')
    return ''.join(parts)

def page_capabilities():
    zh = merge_common({
        "title": "能力全景 · Fenixd",
        "hero.eyebrow": "CAPABILITIES", "hero.h1": '<span class="grad-text">能力全景</span>',
        "hv.1.t": "需求与治理", "hv.2.t": "实现与验证", "hv.3.t": "调度与运维", "hv.4.t": "观测与协作",
        "hero.lede": "从一句自然语言的需求到可上线生产产品的全程。按「需求 / 交付 / 运维 / 观测」四组展开，共 13 项能力。",
        "grp.1.t": "需求与治理", "grp.1.d": "把话说清楚，把口子守住",
        "grp.2.t": "实现与验证", "grp.2.d": "干活的是 Agent，验收的是证据",
        "grp.3.t": "调度与运维", "grp.3.d": "看不见的手，看得见的兜底",
        "grp.4.t": "观测与协作", "grp.4.d": "全过程可视，全状态可查",
        "cap.more": "文档详解 ",
        "c14.t": "知识蒸馏 · 约束持续增强", "c14.tag": "knowledge",
        "c14.d": "每个 SPEC 收工后，其验收断言与能力规则回沉为 .fenix/ 知识域（截图：知识真相源页，按能力域组织、40+ 项能力持续累积）。下一次同类需求自动继承历史约束，框架不是越用越旧，而是越用越懂你的项目；专家经验从人脑与聊天记录蒸馏为机器可执行的规则。",
        "shot.kb": "知识真相源, 按能力域组织的项目知识",
        "shot.c1": "SPEC 详情页, 结构化项目信息与任务清单",
        "shot.c5": "SPEC 列表, Status / Verify / Duration 一目了然",
        "shot.c7": "Command Center, Agent 实例、成功率与今日活动",
        "shot.c9": "Ops 处置链, 升级水位与告警记录",
        "shot.c11": "跨项目总览, SPEC 总量、任务进度与 Token",
"c1.t": "SPEC 生成器", "c1.tag": "/fenix-new", "c1.d": "一句话需求进来，需求 Agent 负责澄清、复杂度评估与时机确认，产出完整 SPEC，提案、设计、需求规格、任务清单四件套，全部落盘可审查。任务清单逐条带验收口径，实现进度以任务完成度量化呈现（截图中 22/22）；执行模式按复杂度建议 fast-track 或 full。SPEC 是后续一切环节的契约锚点：人审的是它，机器执行的也是它。",
        "c2.t": "方案评审门禁", "c2.tag": "spec-review", "c2.d": "SPEC 完成后并不直接开工：评审 Agent 以只读方式从目的适配性、漏洞、回归风险三个维度做单轮评审，可行放行、方向性风险转人工裁决、轻量 SPEC 走白名单直通。评审意见与裁决记录留档可溯。评审不是仪式：它是意图与实现之间的第一道人工门禁。",
        "c3.t": "晋升与产物守卫", "c3.tag": "gates", "c3.d": "声明与产物逐条机械对账：规格 lint 预检拦截草案缺陷，晋升门禁校验状态转移合法性，交付物硬门与收工守卫核对「说过的都做到」。对账零 LLM 参与，规则是确定性的，产物不许说谎，说谎即拦下。",
        "c4.t": "实现者", "c4.tag": "implementer", "c4.d": "实现 Agent 在独立 git worktree 里按 tasks.md 逐条实现并自测，收工受交付物守卫对账，禁止越界改动。简单需求走 fast-track 单 Agent 直达；复杂变更由多 Agent 分段实现，每一段都留下可审查的提交轨迹。",
        "c5.t": "验证引擎", "c5.tag": "verify", "c5.d": "规划器按 SPEC 生成验收场景，零 LLM 引擎逐条执行：web 用 Playwright 驱动真实浏览器、api 发真实 HTTP 请求断言、cli 校验进程输出与退出码。验证结果以计数呈现（截图中 Verify 15/15），连同耗时一并落在 SPEC 列表与详情里，机械正确性不靠模型自觉，靠断言跑出来。",
        "c6.t": "裁决器", "c6.tag": "adjudicator", "c6.d": "验证引擎只产出数据，裁决器给出带证据的 verdict：通过、打回或升级。裁决绝不信任实现 Agent 的自我汇报，「说我做完了」不算数，断言通过才算数。缺陷带着证据进入打回修复循环，而不是消失在聊天记录里。",
        "c7.t": "PM 引擎", "c7.tag": "scheduler", "c7.d": "PM 引擎按优先级、依赖与并发上限调度全项目 SPEC：预算闸门控制单 SPEC 成本，失败退避与自动恢复处理运行期故障。Command Center 把 12 类 Agent 的实例数、成功率与今日活动聚合为编排视图（截图），调度决策有依据，资源水位可观察。",
        "c8.t": "Worktree 管理", "c8.tag": "merge-back", "c8.d": "每次实现在独立 worktree 与分支上进行，主干永远干净。收工 merge-back 自动合并回主干：冲突走自愈或修复通道，反复失败熔断停靠人工；已合并分支自动回收，worktree 生命周期全程由框架托管。",
        "c9.t": "自愈链", "c9.tag": "arbiter", "c9.d": "Administrator 监视困境信号（重复失败、预算耗尽、依赖卡死）并按处置链自动处置；处置不了交 Arbiter 自主裁决，仍不行升级人工告警并在 Dashboard 横幅提示。Ops 页（截图）实时呈现处置链、升级水位与签名配额，自愈不是黑盒，每一步可见。",
        "c10.t": "进程托管", "c10.tag": "supervisor", "c10.d": "daemon 由 supervisor 托管、systemd unit 承载：开机自启、崩溃自动拉起，restart_request 信号式优雅重启保证状态不丢，看门狗守护存活。托管细节对用户透明，可靠性不依赖任何人记得手动拉起服务。",
        "c11.t": "Web Dashboard", "c11.tag": ":8787", "c11.d": "跨项目实时面板：总览、项目、配置、Ops、Command Center 五视图呈现 SPEC 流转、验证产物、Token 消耗与告警。总览页（截图）聚合各项目 SPEC 总量、任务进度与 Agent 水位；详情页可下钻到单个 SPEC 的信息、文档与任务清单。数据直接来自 .fenix/ 状态文件，无额外数据库。",
        "c12.t": "日志与流转录", "c12.tag": ".fenix", "c12.d": "结构化日志与每次 Agent 运行的实时流转录落盘 .fenix/ 目录：谁在何时读了什么、改了什么、为何决策，全部可回放。出问题读文件即重建现场，不依赖任何人的记忆或聊天记录，可追溯性是治理的地基。",
        "c13.t": "CLI 与 Skill 体系", "c13.tag": "/fenix-*", "c13.d": "立项、原型、评审、审批、归档、状态查询全部走 /fenix-* skill：人为代理提供标准入口，daemon 自动拾取文件变化驱动流转。人只在门禁处出手，批准推送、裁决升级、评审原型；其余时间，循环自己转。",
        "lc.eyebrow": "LIFECYCLE", "lc.title": "11 态状态机，全程合法转移",
        "lc.lede": "状态唯一真源是仓库里的 .fenix/STATE.md，文件锁 + 原子写；非法转移直接拒绝。",
        "lc.note": "状态全景图, 依据 fenixd 帮助文档《生命周期与状态机》绘制；唯一状态真源为 .fenix/STATE.md。",
        "arch.eyebrow": "ARCHITECTURE", "arch.title": "薄内核，文件即状态",
        "arch.lede": "没有数据库、没有服务集群；读一遍文件就能重建全部现场，从上次中断处继续。",
        "arch.1.t": "编排核心 · daemon 单进程",
        "arch.2.t": "状态与文件 · .fenix/",
        "arch.3.t": "外围设施",
        "arch.i1": "EventBus", "arch.i1d": "2s 文件监听 + 30min 兜底扫描感知状态变化",
        "arch.i2": "PM Engine", "arch.i2d": "优先级 / 预算 / 重试 / 恢复的调度决策",
        "arch.i3": "AgentRunner", "arch.i3d": "经 HarnessAdapter 拉起 12 类角色 Agent 子进程",
        "arch.i4": "WorktreeManager", "arch.i4d": "隔离 worktree 与 merge-back",
        "arch.j1": "STATE.md", "arch.j1d": "唯一状态真源，文件锁 + 原子写",
        "arch.j2": "配置与日志", "arch.j2d": "config.yaml 分级合并热更新；结构化日志与流转录",
        "arch.j3": "验证产物", "arch.j3d": "场景集、断言结果与截图落盘可追溯",
        "arch.k1": "systemd + supervisor", "arch.k1d": "开机常驻、优雅重启、看门狗",
        "arch.k2": "Dashboard :8787", "arch.k2d": "跨项目实时可视化面板",
        "arch.k3": "claude ↔ dsh 双通道", "arch.k3d": "执行通道可切换，SpawnSpec 进、归一化事件出",
        "arch.m.lede": "需求 Agent 立项时评估复杂度并给出明确建议；简单需求快跑，复杂改动多 Agent 分段。两者共用同一套验证门禁。",
        "mode.1.t": "fast-track · 快速路径", "mode.1d": "单 Agent 一次完成实现与验证，更快更省，适合单点小改动、无 UI / 无迁移、场景数少的简单需求。",
        "mode.2.t": "full · 完整模式", "mode.2d": "多 Agent 分段实现与独立验证，适合跨模块、含 UI 交互、涉状态机与回归的复杂改动。两者共用同一套验证门禁。",
    })
    en = merge_common_en({
        "title": "Capabilities · Fenixd",
        "hero.eyebrow": "CAPABILITIES", "hero.h1": '<span class="grad-text">The capability map</span>',
        "hv.1.t": "Requirements & Governance", "hv.2.t": "Implementation & Verification", "hv.3.t": "Scheduling & Operations", "hv.4.t": "Observability & Collaboration",
        "hero.lede": "The full journey from one natural-language requirement to production-ready software, in four groups: requirements / delivery / operations / observability. 13 capabilities.",
        "grp.1.t": "Requirements &amp; Governance", "grp.1.d": "Say it clearly, guard the gates",
        "grp.2.t": "Delivery &amp; Verification", "grp.2.d": "Agents do the work; evidence does the acceptance",
        "grp.3.t": "Scheduling &amp; Operations", "grp.3.d": "Invisible hands, visible safety nets",
        "grp.4.t": "Observability &amp; Collaboration", "grp.4.d": "Everything visible, every state queryable",
        "cap.more": "Docs ",
        "c14.t": "Knowledge Distillation · Constraints Compound", "c14.tag": "knowledge",
        "c14.d": "When a SPEC finishes, its acceptance assertions and capability rules sink back into the .fenix/ knowledge domain (screenshot: the knowledge source-of-truth page, organized by capability domain, 40+ capabilities and growing). The next similar need inherits historical constraints automatically, the framework does not age with use; it learns your project. Expert experience is distilled from human brains and chat logs into machine-executable rules.",
        "shot.kb": "Knowledge source of truth, organized by capability domain",
        "shot.c1": "SPEC detail, structured project info and task list",
        "shot.c5": "SPEC list, Status / Verify / Duration at a glance",
        "shot.c7": "Command Center, agent instances, success rate and daily activity",
        "shot.c9": "Ops disposition chain, escalations and alerts",
        "shot.c11": "Cross-project overview, SPEC totals and task progress",
"c1.t": "SPEC Generator", "c1.tag": "/fenix-new", "c1.d": "A one-sentence need goes to the requirement agent for clarification, complexity assessment and timing, and comes out as a full SPEC, proposal, design, specs and task list, all on disk and reviewable. Each task carries acceptance criteria, and progress is quantified by task completion (22/22 in the screenshot); execution mode is recommended as fast-track or full by complexity. The SPEC is the contract anchor for everything downstream: humans review it, machines execute it.",
        "c2.t": "Design Review Gate", "c2.tag": "spec-review", "c2.d": "A finished SPEC does not start implementation right away: a review agent makes a single read-only pass over fitness, defects and regression risk, viable passes, directional risk escalates to humans, lightweight SPECs fast-track through a whitelist. Review opinions and adjudication records are kept on disk. Review is not a ceremony: it is the first human gate between intent and implementation.",
        "c3.t": "Promotion &amp; Artifact Guards", "c3.tag": "gates", "c3.d": "Declarations and artifacts are reconciled item by item, mechanically: spec lint pre-checks intercept draft defects, promotion gates validate state-transition legality, and deliverable hard-gates plus finish-guards verify that everything promised was actually done. Zero LLM involvement, the rules are deterministic. Artifacts may not lie; lying means being blocked.",
        "c4.t": "Implementer", "c4.tag": "implementer", "c4.d": "The implementer agent works inside an isolated git worktree, implementing tasks.md item by item with self-tests, reconciled by the finish guard, out-of-scope changes are forbidden. Simple needs take the single-agent fast-track; complex changes are segmented across multiple agents, each segment leaving a reviewable commit trail.",
        "c5.t": "Verify Engine", "c5.tag": "verify", "c5.d": "The planner derives acceptance scenarios from the SPEC; a zero-LLM engine executes each one: web drives a real browser via Playwright, api fires real HTTP requests with assertions, cli checks process output and exit codes. Results appear as counts (Verify 15/15 in the screenshot) alongside duration, in both the SPEC list and detail views, mechanical correctness comes from running assertions, not from model self-discipline.",
        "c6.t": "Adjudicator", "c6.tag": "adjudicator", "c6.d": "The verify engine only produces data; the adjudicator issues an evidence-backed verdict: pass, bounce back, or escalate. It never trusts the implementer's self-report, \"I say it's done\" counts for nothing; passing assertions count for everything. Defects enter the bounce-back loop with their evidence attached, instead of vanishing into chat history.",
        "c7.t": "PM Engine", "c7.tag": "scheduler", "c7.d": "The PM engine schedules every SPEC in the project by priority, dependencies and concurrency: budget gates cap per-SPEC cost, failure backoff and auto-recovery handle runtime faults. The Command Center aggregates instances, success rates and daily activity of 12 agent roles into one orchestration view (screenshot), scheduling decisions have evidence, resource levels are observable.",
        "c8.t": "Worktree Manager", "c8.tag": "merge-back", "c8.d": "Every implementation runs in its own worktree and branch, keeping main always clean. On completion, merge-back folds the branch into main automatically: conflicts go through self-healing or fix channels, repeated failure trips the circuit breaker and parks for a human. Merged branches are recycled automatically, the whole worktree lifecycle is framework-managed.",
        "c9.t": "Self-Healing Chain", "c9.tag": "arbiter", "c9.d": "The Administrator watches for dead-end signals (repeated failures, exhausted budgets, stuck dependencies) and acts along a disposition chain automatically; unresolved cases go to Arbiter adjudication, then to human alerting with a dashboard banner. The Ops page (screenshot) shows disposition chains, escalation levels and signature quotas in real time, self-healing is not a black box; every step is visible.",
        "c10.t": "Process Custody", "c10.tag": "supervisor", "c10.d": "The daemon is supervisor-managed under a systemd unit: it starts on boot, restarts automatically after crashes, does signal-based graceful restarts via restart_request without losing state, and is kept alive by a watchdog. Custody is transparent to the user, reliability never depends on someone remembering to start a service.",
        "c11.t": "Web Dashboard", "c11.tag": ":8787", "c11.d": "A cross-project live panel in five views, Overview, Projects, Config, Ops and Command Center, covering SPEC transitions, verification artifacts, token usage and alerts. The overview (screenshot) aggregates per-project SPEC totals, task progress and agent levels; detail pages drill down to a single SPEC's info, document and task list. Data comes straight from .fenix/ state files, no extra database.",
        "c12.t": "Logs &amp; Transcripts", "c12.tag": ".fenix", "c12.d": "Structured logs and a live run transcript for every agent run land under .fenix/: who read what and when, what changed, and why decisions were made, all replayable. When something breaks, reading files rebuilds the scene, no reliance on memory or chat history. Traceability is the foundation of governance.",
        "c13.t": "CLI &amp; Skill System", "c13.tag": "/fenix-*", "c13.d": "Intake, prototyping, review, approval, archiving and status all run through /fenix-* skills: humans get a standard entry point, and the daemon auto-picks up file changes to drive transitions. People act only at gates, approving pushes, adjudicating escalations, reviewing prototypes. The rest of the time, the loop runs itself.",
        "lc.eyebrow": "LIFECYCLE", "lc.title": "11 states, legal transitions only",
        "lc.lede": "The single source of state is .fenix/STATE.md in the repo, file-locked, atomically written; illegal transitions are rejected outright.",
        "lc.note": "State panorama, drawn from the fenixd lifecycle docs; the single source of truth is .fenix/STATE.md.",
        "arch.eyebrow": "ARCHITECTURE", "arch.title": "Thin kernel, state as files",
        "arch.lede": "No database, no service cluster; reading the files once rebuilds the entire scene and resumes where it left off.",
        "arch.1.t": "Orchestration core · single-process daemon",
        "arch.2.t": "State &amp; files · .fenix/",
        "arch.3.t": "Peripherals",
        "arch.i1": "EventBus", "arch.i1d": "2s file watching + 30min fallback scan on state changes",
        "arch.i2": "PM Engine", "arch.i2d": "Scheduling decisions: priority / budget / retry / recovery",
        "arch.i3": "AgentRunner", "arch.i3d": "Spawns 12 agent roles via HarnessAdapter subprocesses",
        "arch.i4": "WorktreeManager", "arch.i4d": "Isolated worktrees and merge-back",
        "arch.j1": "STATE.md", "arch.j1d": "The single source of state; file lock + atomic write",
        "arch.j2": "Config &amp; logs", "arch.j2d": "config.yaml merged &amp; hot-reloaded; structured logs and transcripts",
        "arch.j3": "Verification artifacts", "arch.j3d": "Scenario sets, assertion results and screenshots, all on disk",
        "arch.k1": "systemd + supervisor", "arch.k1d": "Resident at boot, graceful restart, watchdog",
        "arch.k2": "Dashboard :8787", "arch.k2d": "Cross-project live visualization",
        "arch.k3": "claude ↔ dsh channels", "arch.k3d": "Switchable execution channel: SpawnSpec in, normalized events out",
        "arch.m.lede": "The requirement agent assesses complexity and recommends explicitly; simple needs run fast, complex changes run in segments. Both share the same verification gates.",
        "mode.1.t": "fast-track", "mode.1d": "A single agent implements and verifies in one pass, faster and cheaper; for point changes with no UI/migration and few scenarios.",
        "mode.2.t": "full", "mode.2d": "Multiple agents implement in segments with independent verification, for cross-module changes with UI, state machines and regression concerns. Both share the same verification gates.",
    })
    i18n = {"zh": merge_common(zh), "en": merge_common_en(en)}

    def cap_card(i, ic, shot=None):
        if shot:
            f, ck = shot
            return f'''<article class="card card-featured" data-proto-id="cap-card-{i}">
  <div class="card-body">
    <div class="card-head"><div class="card-ic">{icon(ic)}</div><h3 data-i18n="c{i}.t">…</h3></div>
    <span class="tag ember mono" style="align-self:flex-start" data-i18n="c{i}.tag">…</span>
    <p data-i18n="c{i}.d">…</p>
    <a class="card-link" href="docs.html" data-i18n="cap.more">文档详解 {icon("arrow","ic")}</a>
  </div>
  <figure class="card-shot" data-proto-id="cap-shot-{i}">
    <img src="assets/{f}" alt="">
    <figcaption data-i18n="{ck}">…</figcaption>
  </figure>
</article>'''''
        return f'''<article class="card" data-proto-id="cap-card-{i}">
  <div class="card-head"><div class="card-ic">{icon(ic)}</div><h3 data-i18n="c{i}.t">…</h3></div>
  <span class="tag ember mono" style="align-self:flex-start" data-i18n="c{i}.tag">…</span>
  <p data-i18n="c{i}.d">…</p>
  <a class="card-link" href="docs.html" data-i18n="cap.more">文档详解 {icon("arrow","ic")}</a>
</article>'''

    groups = [
        ("cap-group-governance", "grp.1.t", "grp.1.d",
         [(1, "lu-file-text", ("dash-spec-detail.png", "shot.c1")), (2, "lu-shield-check", None), (3, "lu-list-checks", None)]),
        ("cap-group-delivery", "grp.2.t", "grp.2.d",
         [(4, "lu-git-merge", None), (5, "lu-badge-check", ("dash-project-specs.png", "shot.c5")), (6, "lu-scale", None)]),
        ("cap-group-ops", "grp.3.t", "grp.3.d",
         [(7, "lu-calendar-clock", ("dash-command.png", "shot.c7")), (8, "lu-git-branch", None),
          (9, "lu-heart-pulse", ("dash-activities.png", "shot.c9")), (10, "lu-server", None)]),
        ("cap-group-observe", "grp.4.t", "grp.4.d",
         [(11, "lu-layout-dashboard", ("dash-overview.png", "shot.c11")), (12, "lu-scroll-text", None), (13, "lu-square-terminal", None),
          (14, "book", ("dash-knowledge.png", "shot.kb"))]),
    ]
    group_html = "".join(
        f'''<div class="doc-group" id="{gid}" data-proto-id="{gid}">
  <div class="grp-head"><h3><span data-i18n="{t}">…</span></h3><span class="grp-lede" data-i18n="{d}">…</span><span class="cnt">{len(cards)} caps</span></div>
  <div class="grid-3 caps-grid" data-proto-id="{gid}-grid">{''.join(cap_card(i, ic, shot) for i, ic, shot in cards)}</div>
</div>'''
        for gid, t, d, cards in groups)

    lc_svg = lifecycle_svg()

    def arch_col(gid, title_key, items):
        lis = "".join(
            f'<div class="arch-item" data-proto-id="{gid}-{k}"><b data-i18n="{t}">…</b>'
            f'<span data-i18n="{d}">…</span></div>' for k, t, d in items)
        return f'''<div class="arch-col" data-proto-id="{gid}">
  <h4 data-i18n="{title_key}">…</h4>{lis}</div>'''
    arch_html = (
        arch_col("cap-arch-core", "arch.1.t",
                 [("i1","arch.i1","arch.i1d"),("i2","arch.i2","arch.i2d"),
                  ("i3","arch.i3","arch.i3d"),("i4","arch.i4","arch.i4d")])
        + arch_col("cap-arch-state", "arch.2.t",
                 [("j1","arch.j1","arch.j1d"),("j2","arch.j2","arch.j2d"),
                  ("j3","arch.j3","arch.j3d")])
        + arch_col("cap-arch-periph", "arch.3.t",
                 [("k1","arch.k1","arch.k1d"),("k2","arch.k2","arch.k2d"),
                  ("k3","arch.k3","arch.k3d"),("m1","mode.1.t","mode.1d"),
                  ("m2","mode.2.t","mode.2d")]))

    content = f"""
<section class="hero" data-proto-id="cap-hero">
  <div class="wrap hero-split">
    <div class="hero-copy">
      <p class="eyebrow" data-i18n="hero.eyebrow">CAPABILITIES</p>
      <h1 style="font-size:44px;line-height:1.2;margin:0 0 18px;font-weight:800" data-i18n="hero.h1">…</h1>
      <p class="lede" data-i18n="hero.lede">…</p>
    </div>
    <div class="hero-vis" data-proto-id="cap-hero-vis">
      <a class="hv-card" href="#cap-group-governance" data-proto-id="cap-hero-vis-1">
        <div class="hv-head"><span class="hv-ic">{icon("lu-file-text")}</span><span class="hv-t" data-i18n="hv.1.t">需求与治理</span></div>
        <span class="hv-d" data-i18n="grp.1.d">…</span>
        <span class="hv-n mono">3 caps</span>
      </a>
      <a class="hv-card" href="#cap-group-delivery" data-proto-id="cap-hero-vis-2">
        <div class="hv-head"><span class="hv-ic">{icon("lu-badge-check")}</span><span class="hv-t" data-i18n="hv.2.t">实现与验证</span></div>
        <span class="hv-d" data-i18n="grp.2.d">…</span>
        <span class="hv-n mono">3 caps</span>
      </a>
      <a class="hv-card" href="#cap-group-ops" data-proto-id="cap-hero-vis-3">
        <div class="hv-head"><span class="hv-ic">{icon("lu-calendar-clock")}</span><span class="hv-t" data-i18n="hv.3.t">调度与运维</span></div>
        <span class="hv-d" data-i18n="grp.3.d">…</span>
        <span class="hv-n mono">4 caps</span>
      </a>
      <a class="hv-card" href="#cap-group-observe" data-proto-id="cap-hero-vis-4">
        <div class="hv-head"><span class="hv-ic">{icon("lu-layout-dashboard")}</span><span class="hv-t" data-i18n="hv.4.t">观测与协作</span></div>
        <span class="hv-d" data-i18n="grp.4.d">…</span>
        <span class="hv-n mono">4 caps</span>
      </a>
    </div>
  </div>
</section>

<section class="section" data-proto-id="cap-groups">
  <div class="wrap">
{group_html}
  </div>
</section>


<section class="section" data-proto-id="cap-lifecycle">
  <div class="wrap">
    <p class="eyebrow" data-i18n="lc.eyebrow">LIFECYCLE</p>
    <h2 class="sec-title" data-i18n="lc.title">…</h2>
    <p class="sec-lede" data-i18n="lc.lede">…</p>
    <figure class="lc-figure" data-proto-id="cap-lifecycle-svg">{lc_svg}
      <figcaption><span data-i18n="lc.note">…</span></figcaption>
    </figure>
  </div>
</section>

<section class="section" data-proto-id="cap-architecture">
  <div class="wrap">
    <p class="eyebrow" data-i18n="arch.eyebrow">ARCHITECTURE</p>
    <h2 class="sec-title" data-i18n="arch.title">…</h2>
    <p class="sec-lede" data-i18n="arch.lede">…</p>
    <div class="arch" data-proto-id="cap-arch-grid">{arch_html}</div>
  </div>
</section>

"""
    zh.update({"cta.t": "把你的第一个需求交给Fenixd", "cta.d": "五分钟接入，第一个 SPEC 就能跑通全流程。"})
    en.update({"cta.t": "Hand your first requirement to Fenixd", "cta.d": "Onboard in five minutes; your first SPEC runs the whole loop."})
    return shell("capabilities", "能力全景（原型）", "capabilities", content,
                 {"zh": merge_common(zh), "en": merge_common_en(en)})

# ============================================================ 页面 4：docs.html
def page_docs():
    zh = merge_common({
        "title": "文档中心 · Fenixd",
        "hero.eyebrow": "DOCS", "hero.h1": '<span class="grad-text">文档中心</span>',
        "hero.lede": "12 篇专题 + 3 篇手册构成的帮助文档体系，与 Dashboard「帮助」菜单同源。从第一行安装命令到预算熔断调参，都在这里。",
        "search.ph": "搜索文档：试试「状态机」「预算熔断」「Playwright」…",
        "search.kbd": "Ctrl K",
        "path.eyebrow": "LEARNING PATH", "path.title": "按你的角色选路径",
        "path.1.t": "新手 · 30 分钟跑通第一单",
        "path.1.d": "安装 daemon → 一句话立项 → 看它跑完实现与验证。", "path.1.link": "读：快速上手",
        "path.2.t": "进阶 · 调教你的循环",
        "path.2.d": "验证场景怎么写、预算熔断怎么调、告警怎么分级。", "path.2.link": "读：验证体系",
        "path.3.t": "专家 · 二次开发与通道切换",
        "path.3.d": "claude ↔ dsh 双 harness、知识图谱回填、产物地图。", "path.3.link": "读：DSH 通道运行手册",
        "grp.1.t": "起步", "grp.2.t": "操作", "grp.3.t": "深入", "grp.4.t": "运维与部署",
        "d01.t": "快速上手", "d01.d": "从零到交付的端到端流程",
        "d02.t": "核心概念与架构", "d02.d": "闭环原理、12 类 Agent 角色、full / fast-track 执行模式",
        "d03.t": "生命周期与状态机", "d03.d": "11 状态全景、方案评审门禁、打回修复循环、冻结与恢复",
        "d04.t": "CLI 操作手册", "d04.d": "/fenix-* skill 逐个详解、bin/ 辅助脚本",
        "d08.t": "Dashboard 操作手册", "d08.d": "五页面板逐面板讲解",
        "d09.t": "配置参考", "d09.d": "config.yaml 全键说明、分级合并与热更新",
        "d05.t": "验证体系详解", "d05.d": "三步验证流水线、verify.yaml 契约、web / cli / api 多形态场景",
        "d06.t": "调度与治理规则", "d06.d": "预算熔断、重试退避、告警分级，那些「看不见的手」",
        "d07.t": "保障机制", "d07.d": "声明 lint、晋升门禁、产物硬门、收工守卫、自愈与告警分级",
        "d10.t": "文件与数据地图", "d10.d": "STATE.md、runs、验证产物，出问题去哪查",
        "d11.t": "日志体系", "d11.d": "各日志的用途、格式、轮转与归档",
        "d12.t": "FAQ 与故障排查", "d12.d": "常见现象 → 根因 → 处置",
        "d14.t": "知识真相源", "d14.d": "spec/knowledge/ 目录契约与回填 / 体检车道",
        "d15.t": "DSH 通道运行手册", "d15.d": "agent 执行通道 claude ↔ dsh 切换与回切",
        "dinst.t": "全新环境部署手册", "dinst.d": "干净 Linux / Windows 机器从零装好 Fenixd，双 harness 全覆盖",
        "tag.topic": "专题", "tag.manual": "手册", "tag.install": "部署",
        "cta.t": "读完了？装一个试试。", "cta.d": "文档再好，不如让循环替你跑一次。",
    })
    en = merge_common_en({
        "title": "Docs · Fenixd",
        "hero.eyebrow": "DOCS", "hero.h1": '<span class="grad-text">The documentation hub</span>',
        "hero.lede": "12 topics + 3 handbooks, kept in sync with the Dashboard's Help menu, from your first install command to tuning budget breakers.",
        "search.ph": "Search docs: try \"state machine\", \"budget breaker\", \"Playwright\"…",
        "search.kbd": "Ctrl K",
        "path.eyebrow": "LEARNING PATH", "path.title": "Pick a path for your role",
        "path.1.t": "Newcomer · first SPEC in 30 minutes",
        "path.1.d": "Install the daemon → file a one-liner → watch it implement and verify.", "path.1.link": "Read: Quick Start",
        "path.2.t": "Practitioner · tune your loop",
        "path.2.d": "Writing verification scenarios, tuning budget breakers, alert levels.", "path.2.link": "Read: Verification",
        "path.3.t": "Expert · hacking &amp; channels",
        "path.3.d": "claude ↔ dsh harness switching, knowledge atlas backfill, artifact maps.", "path.3.link": "Read: DSH Runbook",
        "grp.1.t": "Getting started", "grp.2.t": "Operating", "grp.3.t": "Going deeper", "grp.4.t": "Ops &amp; deployment",
        "d01.t": "Quick Start", "d01.d": "End-to-end flow from zero to delivery",
        "d02.t": "Concepts &amp; Architecture", "d02.d": "Loop principles, 12 agent roles, full / fast-track modes",
        "d03.t": "Lifecycle &amp; State Machine", "d03.d": "All 11 states, review gates, bounce-back loops, freeze &amp; resume",
        "d04.t": "CLI Handbook", "d04.d": "Every /fenix-* skill explained, plus bin/ helpers",
        "d08.t": "Dashboard Handbook", "d08.d": "A guided tour of the five dashboard views",
        "d09.t": "Configuration Reference", "d09.d": "Every config.yaml key, layered merge and hot reload",
        "d05.t": "Verification Deep Dive", "d05.d": "The 3-step pipeline, verify.yaml contract, web / cli / api scenarios",
        "d06.t": "Scheduling &amp; Governance", "d06.d": "Budget breakers, retry backoff, alert levels, the invisible hands",
        "d07.t": "Safeguards", "d07.d": "Declaration lint, promotion gates, artifact hard-gates, finish guards, self-healing",
        "d10.t": "Files &amp; Data Map", "d10.d": "STATE.md, runs, verification artifacts, where to look when in doubt",
        "d11.t": "Logging", "d11.d": "Purpose, format, rotation and archival of every log",
        "d12.t": "FAQ &amp; Troubleshooting", "d12.d": "Common symptoms → root causes → fixes",
        "d14.t": "Knowledge Atlas", "d14.d": "The spec/knowledge/ contract and its backfill lanes",
        "d15.t": "DSH Channel Runbook", "d15.d": "Switching the agent channel between claude and dsh",
        "dinst.t": "Fresh Deployment Guide", "dinst.d": "Set up Fenixd on a clean Linux / Windows machine, both harnesses",
        "tag.topic": "Topic", "tag.manual": "Handbook", "tag.install": "Deploy",
        "cta.t": "Done reading? Install one.", "cta.d": "Docs are good. Letting the loop run once is better.",
    })
    # 真实 help 文档元数据注入（标题/摘要取自 /root/fenixd/docs/help/*.md）
    for no, fname in FMAP.items():
        k = "dinst" if no == "00" else f"d{no}"
        t, d = help_meta(no, fname)
        zh[f"{k}.t"], zh[f"{k}.d"] = t, d
        en[f"{k}.t"], en[f"{k}.d"] = t, d
    i18n = {"zh": merge_common(zh), "en": merge_common_en(en)}

    paths = [("docs-path-1", "path.1.t", "path.1.d", "path.1.link", "help/01-quick-start.html"),
             ("docs-path-2", "path.2.t", "path.2.d", "path.2.link", "help/05-verification.html"),
             ("docs-path-3", "path.3.t", "path.3.d", "path.3.link", "help/15-dsh-harness-runbook.html")]
    paths_html = "".join(
        f'''<div class="path-card" data-proto-id="{pid}">
  <div class="step mono">STEP {i+1}</div>
  <h3 data-i18n="{t}">…</h3><p data-i18n="{d}">…</p>
  <a class="card-link" href="{plink}" data-i18n="{lk}">…</a>
</div>''' for i, (pid, t, d, lk, plink) in enumerate(paths))

    docs = [
        ("01","d01","topic"),("02","d02","topic"),("03","d03","topic"),
        ("04","d04","manual"),("08","d08","manual"),("09","d09","topic"),
        ("05","d05","topic"),("06","d06","topic"),("07","d07","topic"),
        ("10","d10","topic"),("11","d11","topic"),("12","d12","topic"),
        ("14","d14","topic"),("15","d15","manual"),("00","dinst","install"),
    ]
    def dcard(no, k, tagk, i):
        n = "INSTALL" if no == "00" else f"{no} · HELP"
        return f'''<a class="doc-card" href="help/{FMAP[no].replace(".md", ".html")}" data-proto-id="docs-card-{k}">
  <span class="no mono">{n} · <span data-i18n="tag.{tagk}">专题</span></span>
  <span class="tt" data-i18n="{k}.t">…</span>
  <span class="ds" data-i18n="{k}.d">…</span>
</a>'''
    groups = [
        ("docs-group-start", "grp.1.t", [("01","d01","topic",1),("02","d02","topic",2),("03","d03","topic",3)]),
        ("docs-group-operate", "grp.2.t", [("04","d04","manual",4),("08","d08","manual",5),("09","d09","topic",6)]),
        ("docs-group-deep", "grp.3.t", [("05","d05","topic",7),("06","d06","topic",8),("07","d07","topic",9)]),
        ("docs-group-ops", "grp.4.t", [("10","d10","topic",10),("11","d11","topic",11),("12","d12","topic",12),
                                        ("14","d14","topic",13),("15","d15","manual",14),("13","d13","manual",15),
                                        ("00","dinst","install",16)]),
    ]
    groups_html = "".join(
        f'''<div class="doc-group" data-proto-id="{gid}">
  <h3><span data-i18n="{t}">…</span><span class="cnt">{len(cards)}</span></h3>
  <div class="doc-grid">{''.join(dcard(*c) for c in cards)}</div>
</div>''' for gid, t, cards in groups)

    content = f"""
<section class="hero" style="padding-bottom:56px" data-proto-id="docs-hero">
  <div class="wrap">
    <p class="eyebrow" data-i18n="hero.eyebrow">DOCS</p>
    <h1 style="font-size:44px;line-height:1.2;margin:0 0 18px;font-weight:800" data-i18n="hero.h1">…</h1>
    <p class="lede" data-i18n="hero.lede">…</p>
    <div class="doc-search" data-proto-id="docs-search">
      {icon("search")}
      <input type="search" data-i18n-ph="search.ph" placeholder="搜索文档…（原型，搜索未接通）" aria-label="搜索文档">
      <kbd class="mono" data-i18n="search.kbd">Ctrl K</kbd>
    </div>
  </div>
</section>

<section class="section" data-proto-id="docs-path">
  <div class="wrap">
    <p class="eyebrow" data-i18n="path.eyebrow">LEARNING PATH</p>
    <h2 class="sec-title" data-i18n="path.title">…</h2>
    <div class="path-row" style="margin-top:32px" data-proto-id="docs-path-row">{paths_html}</div>
{groups_html}    </div>
  </div>
</section>
"""
    return shell("docs", "文档中心（原型）", "docs", content,
                 {"zh": merge_common(zh), "en": merge_common_en(en)})

# ============================================================ 页面 5：community.html
def page_community():
    zh = merge_common({
        "title": "社区 · Fenixd",
        "hero.eyebrow": "COMMUNITY", "hero.h1": '<span class="grad-text">Fenixd 社区</span>',
        "hero.lede": "Fenixd 在公开仓库中演化：每个 SPEC 都是一次公开的实验，每条状态转移都有据可查。来看看它，或者参与它。",
        "gh.repo": "Fenixd / Fenixd", "gh.desc": "Fenix Loop Engineering Framework，Harness 中立的自动化软件开发循环框架（支持 Claude Code、DSH 等）。本仓库由 Fenixd 自身驱动演进。",
        "gh.s1": "stars（示例）", "gh.s2": "forks（示例）", "gh.s3": "issues", "gh.s4": "语言",
        "gh.clone": "git clone",
        "gh.b1": "查看仓库", "gh.b2": "提交 Issue",
        "side.1.t": "Discussions", "side.1.d": "用法讨论、案例分享、路线图共创",
        "side.2.t": "缺陷反馈", "side.2.d": "带 .fenix/ 产物与日志的 issue 模板，定位更快",
        "side.3.t": "发布订阅", "side.3.d": "Release 与更新日志通知",
        "side.4.t": "微信交流群", "side.4.d": "中文用户群，入口见 README（示例）",
        "road.eyebrow": "RELEASE NOTES", "road.title": "近期动态",
        "road.1.v": "v0.9.x", "road.1.t": "打回修复循环收敛率提升", "road.1.d": "预算熔断阈值分级细化，回归率显著下降（示例数据）",
        "road.2.v": "v0.8.x", "road.2.t": "验证引擎多形态扩展", "road.2.d": "web / api / cli 三形态场景 runner，Playwright 截图对比入列（示例数据）",
        "road.3.v": "v0.7.x", "road.3.t": "知识真相源上线", "road.3.d": "spec/knowledge/ 能力域目录 + 回填体检车道（示例数据）",
        "road.link": "查看完整更新日志",
        "ct.eyebrow": "CONTRIBUTE", "ct.title": "参与贡献",
        "ct.lede": "从一句话 issue 到核心模块 PR，每个层级的参与都被欢迎，毕竟，这个项目最擅长把一句话变成完整交付。",
        "ct.1.t": "报告缺陷", "ct.1.d": "按 issue 模板附上 .fenix/ 产物，缺陷修复车道会按批消化",
        "ct.2.t": "改进文档", "ct.2.d": "docs/help/ 与 Dashboard 帮助菜单同源，勘误即是贡献",
        "ct.3.t": "提交 PR", "ct.3.d": "核心改动同样走 SPEC 流程，请先开 issue 对齐意图",
        "ct.4.t": "分享案例", "ct.4.d": "在 Discussions 发布你的 SPEC 实录与调参经验",
    })
    en = merge_common_en({
        "title": "Community · Fenixd",
        "hero.eyebrow": "COMMUNITY", "hero.h1": '<span class="grad-text">The Fenixd community</span>',
        "hero.lede": "Fenixd evolves in the open: every SPEC is a public experiment, every state transition is on the record. Come look, or take part.",
        "gh.repo": "Fenixd / Fenixd", "gh.desc": "Fenix Loop Engineering Framework, a harness-neutral automated software development loop framework (Claude Code, DSH and more). This repo is driven by Fenixd itself.",
        "gh.s1": "stars (sample)", "gh.s2": "forks (sample)", "gh.s3": "issues", "gh.s4": "language",
        "gh.clone": "git clone",
        "gh.b1": "Open repository", "gh.b2": "File an issue",
        "side.1.t": "Discussions", "side.1.d": "Usage Q&amp;A, case studies, roadmap co-design",
        "side.2.t": "Bug reports", "side.2.d": "An issue template with .fenix/ artifacts and logs locates defects faster",
        "side.3.t": "Release feed", "side.3.d": "Release &amp; changelog notifications",
        "side.4.t": "WeChat group", "side.4.d": "Chinese user group; entry in README (sample)",
        "road.eyebrow": "RELEASE NOTES", "road.title": "Recent updates",
        "road.1.v": "v0.9.x", "road.1.t": "Bounce-back loop converges better", "road.1.d": "Tiered budget-breaker thresholds; regression rate down sharply (sample data)",
        "road.2.v": "v0.8.x", "road.2.t": "Verification engine multi-modal", "road.2.d": "web / api / cli scenario runners; Playwright screenshot diffing (sample data)",
        "road.3.v": "v0.7.x", "road.3.t": "Knowledge atlas lands", "road.3.d": "spec/knowledge/ domain index + backfill lanes (sample data)",
        "road.link": "Full changelog (sample)",
        "ct.eyebrow": "CONTRIBUTE", "ct.title": "Get involved",
        "ct.lede": "From a one-line issue to a core-module PR, every level of participation is welcome, after all, turning one sentence into a full delivery is what this project does best.",
        "ct.1.t": "Report bugs", "ct.1.d": "Attach .fenix/ artifacts per the issue template; the code-fix lane digests them in batches",
        "ct.2.t": "Improve docs", "ct.2.d": "docs/help/ mirrors the Dashboard Help menu, a typo fix is a contribution",
        "ct.3.t": "Send PRs", "ct.3.d": "Core changes follow the SPEC flow too, open an issue to align first",
        "ct.4.t": "Share cases", "ct.4.d": "Publish your SPEC case studies and tuning notes in Discussions",
    })
    i18n = {"zh": merge_common(zh), "en": merge_common_en(en)}

    sides = [(1, "chat"), (2, "alert"), (3, "zap"), (4, "users")]
    sides_html = "".join(
        f'''<div class="mini-card" data-proto-id="comm-side-{i}">
  <div class="card-ic">{icon(ic)}</div>
  <div><h4 data-i18n="side.{i}.t">…</h4><p data-i18n="side.{i}.d">…</p></div>
</div>''' for i, ic in sides)

    roads = [(1,), (2,), (3,)]
    roads_html = "".join(
        f'''<div class="roadmap-item" data-proto-id="comm-road-{i}">
  <span class="ver mono" data-i18n="road.{i}.v">…</span>
  <div class="bd"><h4 data-i18n="road.{i}.t">…</h4><p data-i18n="road.{i}.d">…</p></div>
</div>''' for (i,) in roads)

    contributes = [(1, "alert"), (2, "book"), (3, "branch"), (4, "chat")]
    contributes_html = "".join(
        f'''<article class="card" data-proto-id="comm-ct-{i}">
  <div class="card-ic">{icon(ic)}</div>
  <h3 data-i18n="ct.{i}.t">…</h3><p data-i18n="ct.{i}.d">…</p>
</article>''' for i, ic in contributes)

    content = f"""
<section class="hero" data-proto-id="comm-hero">
  <div class="wrap">
    <p class="eyebrow" data-i18n="hero.eyebrow">COMMUNITY</p>
    <h1 style="font-size:44px;line-height:1.2;margin:0 0 18px;font-weight:800" data-i18n="hero.h1">…</h1>
    <p class="lede" style="max-width:none" data-i18n="hero.lede">…</p>
  </div>
</section>

<section class="section" data-proto-id="comm-github">
  <div class="wrap">
    <div class="gh-card" data-proto-id="comm-gh-card">
      <div class="gh-main" data-proto-id="comm-gh-main">
        <div class="repo">{icon("github")}<span data-i18n="gh.repo">Fenixd / Fenixd</span></div>
        <p style="color:var(--text-2);font-size:14.5px;margin:12px 0 0" data-i18n="gh.desc">…</p>
        <div class="gh-stats" data-proto-id="comm-gh-stats">
          <div class="s"><div class="v num">2.1k</div><div class="k" data-i18n="gh.s1">…</div></div>
          <div class="s"><div class="v num">318</div><div class="k" data-i18n="gh.s2">…</div></div>
          <div class="s"><div class="v num">47</div><div class="k" data-i18n="gh.s3">…</div></div>
          <div class="s"><div class="v num">Python</div><div class="k" data-i18n="gh.s4">…</div></div>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          <a class="btn btn-ghost btn-sm mono" href="https://github.com/fenixsoft/fenixd.git" data-i18n="gh.clone">git clone</a>
          <a class="btn btn-primary btn-sm" href="https://github.com/fenixsoft/fenixd" data-i18n="gh.b1">查看仓库{icon("arrow")}</a>
        </div>
      </div>
      <div class="gh-side" data-proto-id="comm-side-grid">{sides_html}</div>
    </div>
  </div>
</section>

<section class="section" data-proto-id="comm-roadmap">
  <div class="wrap">
    <p class="eyebrow" data-i18n="road.eyebrow">RELEASE NOTES</p>
    <h2 class="sec-title" data-i18n="road.title">…</h2>
    <div style="border-top:1px solid var(--line);margin-top:28px" data-proto-id="comm-road-list">{roads_html}</div>
    <p style="margin-top:18px"><a href="https://github.com/fenixsoft/fenixd/releases" data-i18n="road.link">查看完整更新日志</a></p>
  </div>
</section>

<section class="section" data-proto-id="comm-contribute">
  <div class="wrap">
    <p class="eyebrow" data-i18n="ct.eyebrow">CONTRIBUTE</p>
    <h2 class="sec-title" data-i18n="ct.title">…</h2>
    <p class="sec-lede" data-i18n="ct.lede">…</p>
    <div class="grid-4" data-proto-id="comm-ct-grid">{contributes_html}</div>
    <div class="cta-band" style="margin-top:56px" data-proto-id="comm-cta-band">
      <h2 data-i18n="cta.t">从一个 issue 开始</h2>
      <p data-i18n="cta.d">或者先装一个，让它替你把第一句话变成代码。</p>
      <div class="hero-ctas">
        <a class="btn btn-primary" href="index.html#quickstart" data-i18n="nav.cta">快速开始</a>
        <a class="btn btn-ghost" href="docs.html" data-i18n="nav.docs">文档</a>
      </div>
    </div>
  </div>
</section>
"""
    zh.update({"cta.t": "从一个 issue 开始", "cta.d": "或者先装一个，让它替你把第一句话变成代码。"})
    en.update({"cta.t": "Start from an issue", "cta.d": "Or install one first, let the loop turn your first sentence into code."})
    return shell("community", "社区（原型）", "community", content,
                 {"zh": merge_common(zh), "en": merge_common_en(en)})

# ============================================================ 主流程
PAGES = [
    ("index.html", page_index),
    ("why.html", page_why),
    ("capabilities.html", page_capabilities),
    ("docs.html", page_docs),
    ("community.html", page_community),
]

def main():
    help_dir = os.path.join(OUT_DIR, "help")
    os.makedirs(help_dir, exist_ok=True)
    for f in sorted(os.listdir(HELP_SRC)):
        if f.endswith(".md"):
            page = md_to_html(os.path.join(HELP_SRC, f), f)
            with open(os.path.join(help_dir, f.replace(".md", ".html")), "w", encoding="utf-8") as fh:
                fh.write(page)
    print(f"rendered help pages: {len([f for f in os.listdir(help_dir) if f.endswith('.html')])}")
    for name, fn in PAGES:
        html = fn()
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"wrote {path} ({len(html)} bytes)")

if __name__ == "__main__":
    main()
