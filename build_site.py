#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_site.py · fenixd-website 站点构建管线

以 specs/website-home-primary-pages/prototype/（UI 真相源）为唯一界面来源，构建
零外部依赖的纯静态站点到 site/dist/：

    preflight   校验真相源（五页 / help 16 页 / assets 6 张 / logo / mermaid）与净化标记
    stage       复制五页 + 静态资源（排除原型脚手架文件 annotator.js）
    sanitize    净化三类原型脚手架：仿样横幅（proto-banner）、annotator.js 引用、
                配色 dock（data-proto-id 以 -palette-dock 结尾的元素及其 localStorage 初始化脚本块）
    render_docs 浅克隆 github.com/fenixsoft/fenixd（复用 .site-cache/fenixd），以原型自带的
                渲染管线（md_to_html / help_meta 迁移版）生成 help/*.html，
                docs.html 卡片标题/摘要/篇数同步真实文档
    inject_gh_data  经 GitHub 公共 API 取 fenixsoft/fenixd 真实 stars/forks/open_issues，
                注入 community.html 数据卡前三格（第四格语言为静态值，不动）；
                API 失败降级注入 "--" 并打印 WARN，构建继续
    verify      产物资源引用完整性（img/script/内链 href 目标存在于产物树）
    smoke       本地 http.server 冒烟：五页 + 至少 3 篇 help 页 200，annotator.js 404

构建全部成功后才把临时目录原子替换为 site/dist/，任何一步失败都不产出残缺站点
（非零退出并指明失败子步骤）。标准库实现，无第三方依赖。
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROTO = ROOT / "specs" / "website-home-primary-pages" / "prototype"
SITE = ROOT / "site"
DIST = SITE / "dist"
TMP = SITE / ".tmp-build"
CACHE = ROOT / ".site-cache" / "fenixd"
SRC_REPO_URL = os.environ.get("FENIXD_SRC_URL", "https://github.com/fenixsoft/fenixd")
GH_API_URL = "https://api.github.com/repos/fenixsoft/fenixd"
GITHUB_BLOB_BASE = "https://github.com/fenixsoft/fenixd/blob/main"

PAGES = ["index.html", "why.html", "capabilities.html", "docs.html", "community.html"]
STATIC_FILES = ["logo-64.png", "mermaid.min.js"]
EXPECTED_HELP = [
    "01-quick-start.html", "02-concepts.html", "03-lifecycle.html", "04-cli.html",
    "05-verification.html", "06-governance.html", "07-safeguards.html", "08-dashboard.html",
    "09-config.html", "10-artifacts.html", "11-logs.html", "12-faq.html",
    "13-self-update.html", "14-knowledge-atlas.html", "15-dsh-harness-runbook.html",
    "README.html",
]
EXPECTED_ASSETS = [
    "dash-activities.png", "dash-command.png", "dash-knowledge.png",
    "dash-overview.png", "dash-project-specs.png", "dash-spec-detail.png",
]

# docs.html 文档卡片分组与标签口径（与原型 generator/build_proto.py page_docs() 一致）；
# 真实文档集合变化时，未入表的文档归入最后一个分组（ops），标签默认 topic。
DOC_GROUPS = [
    ("start", "grp.1.t", ["01", "02", "03"]),
    ("operate", "grp.2.t", ["04", "08", "09"]),
    ("deep", "grp.3.t", ["05", "06", "07"]),
    ("ops", "grp.4.t", ["10", "11", "12", "14", "15", "13", "00"]),
]
DOC_TAGS = {"04": "manual", "08": "manual", "15": "manual", "13": "manual", "00": "install"}
# i18n 字典中文档卡键形如 d01.t / d15.d / dinst.t / d16.t
DOC_KEY_RE = re.compile(r"^d(?:\d+|[a-z0-9-]+)\.(?:t|d)$")


class BuildError(Exception):
    """带失败子步骤标签的构建错误（错误信息指明失败子步骤）。"""

    def __init__(self, step: str, msg: str):
        super().__init__(f"{step}: {msg}")
        self.step = step
        self.msg = msg


# ============================================================ 1. preflight
def preflight() -> None:
    missing: list[str] = []
    for name in PAGES:
        if not (PROTO / name).is_file():
            missing.append(name)
    for name in EXPECTED_HELP:
        if not (PROTO / "help" / name).is_file():
            missing.append(f"help/{name}")
    for name in EXPECTED_ASSETS:
        if not (PROTO / "assets" / name).is_file():
            missing.append(f"assets/{name}")
    for name in STATIC_FILES:
        if not (PROTO / name).is_file():
            missing.append(name)
    if missing:
        raise BuildError("preflight", "原型真相源缺件: " + ", ".join(missing))

    issues: list[str] = []
    for name in PAGES:
        text = (PROTO / name).read_text(encoding="utf-8")
        if "proto-banner" not in text:
            issues.append(f"{name} 缺仿样横幅标记 proto-banner")
        if "annotator.js" not in text:
            issues.append(f"{name} 缺 annotator.js 引用")
        if not re.search(r'data-proto-id="[^"]*-palette-dock"', text):
            issues.append(f"{name} 缺配色 dock 锚 -palette-dock")
    if issues:
        raise BuildError("preflight", "净化标记校验失败: " + "; ".join(issues))


# ============================================================ 2. stage
def stage(tmp: Path) -> None:
    tmp.mkdir(parents=True, exist_ok=True)
    for name in PAGES:
        shutil.copyfile(PROTO / name, tmp / name)
    for name in STATIC_FILES:
        shutil.copyfile(PROTO / name, tmp / name)
    (tmp / "assets").mkdir()
    for name in EXPECTED_ASSETS:
        shutil.copyfile(PROTO / "assets" / name, tmp / "assets" / name)
    (tmp / "help").mkdir()
    # annotator.js 属原型脚手架，不复制进站点
    # GitHub Pages 自定义域：CNAME 文件必须位于发布 artifact 根
    cname = Path(__file__).resolve().parent / "CNAME"
    if cname.exists():
        shutil.copyfile(cname, tmp / "CNAME")
    # 机器可读安装入口（harness 按 it 指引安装 fenixd）
    inst = Path(__file__).resolve().parent / "install.md"
    if inst.exists():
        shutil.copyfile(inst, tmp / "install.md")


# ============================================================ 3. sanitize
PAL_DOCK_DIV_RE = re.compile(
    r'<div class="pal-dock" data-proto-id="[A-Za-z0-9-]+-palette-dock"[^>]*>.*?</div>\n?', re.S)
PAL_DOCK_JS_RE = re.compile(
    r"\n  var PAL_DOCK = document\.querySelector\('\.pal-dock'\);.*?\n  \}\n", re.S)
BANNER_DIV_RE = re.compile(r'<div class="proto-banner"[^>]*>.*?</div>\n?', re.S)
BANNER_CSS_RE = re.compile(r"\.proto-banner(?: strong)?\{[^}]*\}\n?")
ANNOTATOR_RE = re.compile(r"<script[^>]*annotator\.js[^>]*></script>\n?")


def sanitize(html: str, page: str) -> str:
    """移除三类原型脚手架；站点内容与交互（i18n / 移动端导航 / 灯箱）不动。"""
    # ① 仿样横幅：div 块 + 同名 CSS 规则（含跨行规则体）
    html, n = BANNER_DIV_RE.subn("", html)
    if n != 1:
        raise BuildError("sanitize", f"{page}: 仿样横幅块匹配 {n} 处（预期 1）")
    html = BANNER_CSS_RE.sub("", html)
    # ② annotator.js script 引用（按 src 含 annotator.js 匹配）
    html, n = ANNOTATOR_RE.subn("", html)
    if n != 1:
        raise BuildError("sanitize", f"{page}: annotator.js 引用匹配 {n} 处（预期 1）")
    # ③ 配色 dock：元素 + 其 localStorage 初始化脚本块
    html, n_div = PAL_DOCK_DIV_RE.subn("", html)
    html, n_js = PAL_DOCK_JS_RE.subn("\n", html)
    if n_div != 1 or n_js != 1:
        raise BuildError("sanitize",
                         f"{page}: 配色 dock 移除异常（div={n_div}, js={n_js}，预期各 1）")

    # 断言：三标记零残留
    for marker in ("proto-banner", "annotator.js", "-palette-dock"):
        if marker in html:
            raise BuildError("sanitize", f"{page}: 净化后仍有残留标记 {marker}")
    # 断言：站点交互完整保留（语言切换 / 移动端导航 / i18n 引擎 / 灯箱）
    kept = ('id="lang-zh"' in html and 'id="lang-en"' in html
            and 'id="nav-burger"' in html and "PROTO_I18N" in html
            and "card-shot" in html)
    if not kept:
        raise BuildError("sanitize", f"{page}: 站点交互元素缺失（语言切换/移动端导航/i18n/灯箱）")
    return set_default_lang(html, page)


# 默认语言英文化（构建层后处理；原型真相源保持中文初显不动）：
# 无 localStorage 偏好的访客首屏英文；手动切换 zh 后仍记忆（localStorage 机制不变）。
# help/*.html 渲染页不参与：文档本体是中文内容，lang="zh" 语义正确。
def set_default_lang(html: str, page: str) -> str:
    subs = [
        ('<html lang="zh-CN"', '<html lang="en"', 1),
        ("var saved = 'zh';", "var saved = 'en';", 1),
        ("localStorage.getItem('fenixd-proto-lang') || 'zh'",
         "localStorage.getItem('fenixd-proto-lang') || 'en'", 1),
    ]
    for old, new, expect in subs:
        n = html.count(old)
        if n != expect:
            raise BuildError("sanitize",
                             f"{page}: 默认语言替换锚「{old[:48]}」匹配 {n} 处（预期 {expect}）")
        html = html.replace(old, new)
    if "|| 'zh'" in html:
        raise BuildError("sanitize", f"{page}: 默认语言替换后仍有 'zh' 回退残留")
    return html


# ============================================================ 4. render_docs
def _run_git(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = tail[-1][:300] if tail else f"exit={proc.returncode}"
        raise BuildError("clone", f"git 命令失败（{' '.join(args[:3])}…）: {detail}")


def sync_clone() -> None:
    """浅克隆 fenixsoft/fenixd 至 .site-cache/fenixd；已存在则 fetch 刷新复用。"""
    if (CACHE / ".git").exists():
        _run_git(["git", "-C", str(CACHE), "fetch", "--depth", "1", "origin", "HEAD"])
        _run_git(["git", "-C", str(CACHE), "reset", "--hard", "FETCH_HEAD"])
    else:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        _run_git(["git", "clone", "--depth", "1", SRC_REPO_URL, str(CACHE)])


# ---- 渲染管线（迁移自原型 generator/build_proto.py，行为不变；HELP_SRC 参数化为克隆路径） ----
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


def _md_inline(t: str, known_stems: frozenset[str]) -> str:
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)

    def _link(m):
        href = m.group(2)
        if not href.startswith(("http://", "https://", "mailto:", "#")):
            base, sep, frag = href.partition("#")
            if base.endswith(".md"):
                stem = base.rstrip("/").rsplit("/", 1)[-1][:-3]
                if stem in known_stems:
                    # 原型管线仅改写裸 .md；站点构建补齐 .md#锚点 互链改写，保证内链完整性（task 2.4）
                    href = base[:-3] + ".html" + ("#" + frag if sep else "")
                else:
                    # 帮助文档集之外的 .md（如 ../install.md）指向源仓库原文
                    repo_path = posixpath.normpath("docs/help/" + base)
                    if not repo_path.startswith(".."):
                        href = f"{GITHUB_BLOB_BASE}/{repo_path}" + ("#" + frag if sep else "")
        return f'<a href="{href}">{m.group(1)}</a>'

    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, t)
    return t


def md_to_html(src: Path, fname: str, known_stems: frozenset[str] = frozenset()) -> str:
    """轻量 markdown→自包含 HTML（标题/段落/fenced 代码/表格/列表/引用/hr/行内样式）"""
    out, i, lines = [], 0, src.read_text(encoding="utf-8").splitlines()
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
            out.append(f"<h{lv}>{_md_inline(m.group(2), known_stems)}</h{lv}>")
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
                head = "".join(f"<th>{_md_inline(c, known_stems)}</th>" for c in buf[0])
                body = "".join("<tr>" + "".join(f"<td>{_md_inline(c, known_stems)}</td>" for c in r) + "</tr>" for r in buf[1:])
                out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", t):
            items, ol = [], bool(re.match(r"^\s*\d+\.", t))
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]).strip())
                i += 1
            tag = "ol" if ol else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_md_inline(x, known_stems)}</li>" for x in items) + f"</{tag}>")
            continue
        if t.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + _md_inline(" ".join(buf), known_stems) + "</blockquote>")
            continue
        buf = [t]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|```|\||\s*([-*]|\d+\.)\s|>|---)", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>" + _md_inline(" ".join(buf), known_stems) + "</p>")
    body_html = "".join(out)
    title = re.search(r"<h1>(.*?)</h1>", body_html)
    t = title.group(1) if title else fname
    doc = (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
           f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{t} · Fenixd 帮助</title>'
           f"<style>{_MD_CSS}</style></head><body>"
           f'<a class="back" href="../docs.html">← 返回文档中心</a>'
           + body_html +
           f'<p class="meta">本页由 Fenixd 仓库 docs/help/{fname} 渲染生成。</p>')
    if 'class="mermaid"' in body_html:
        doc += ('<script src="../mermaid.min.js"></script><script>'
                'mermaid.initialize({startOnLoad:false,theme:"neutral",securityLevel:"strict",'
                'fontFamily:"system-ui,-apple-system,sans-serif",'
                'fontSize:14,themeVariables:{fontSize:"14px"},'
                'sequence:{actorFontSize:14,messageFontSize:14,noteFontSize:14}});'
                'mermaid.run({querySelector:"pre.mermaid"}).catch(function(e){'
                'document.querySelectorAll("pre.mermaid").forEach(function(p){'
                'if(!p.querySelector("svg")){p.classList.add("mm-err");}});});'
                "</script>")
    return doc + "</body></html>"


def help_meta(path: Path) -> tuple[str, str]:
    """读取 help md，返回 (真实标题, 摘要)"""
    lines = path.read_text(encoding="utf-8").splitlines()
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
        t = re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) < 10:
            continue
        digest = (t[:66] + "…") if len(t) > 66 else t
        break
    return title, digest


def build_doc_metas(help_src: Path) -> list[dict]:
    mds = sorted(help_src.glob("*.md"))
    if not mds:
        raise BuildError("render", f"源仓库 docs/help/ 无 markdown 文档（{help_src}）")
    metas = []
    for md in mds:
        stem = md.stem
        if stem == "README":
            no, key, label = "00", "dinst", "INSTALL"
        else:
            prefix = stem.split("-", 1)[0]
            no = prefix if prefix.isdigit() else stem
            key, label = f"d{no}", f"{no} · HELP"
        title, digest = help_meta(md)
        metas.append({"no": no, "key": key, "label": label, "href": f"{stem}.html",
                      "title": title, "digest": digest})
    return metas


def assign_groups(metas: list[dict]) -> dict[str, list[dict]]:
    by_no = {m["no"]: m for m in metas}
    remaining = set(by_no)
    assignment: dict[str, list[dict]] = {}
    for gid, _gkey, nos in DOC_GROUPS:
        assignment[gid] = [by_no[n] for n in nos if n in by_no]
        remaining -= set(nos)
    for no in sorted(remaining):  # 未入表的新文档归入最后一个分组
        assignment["ops"].append(by_no[no])
    return assignment


def _dcard_html(m: dict) -> str:
    tagk = DOC_TAGS.get(m["no"], "topic")
    return (f'<a class="doc-card" href="help/{m["href"]}" data-proto-id="docs-card-{m["key"]}">\n'
            f'  <span class="no mono">{m["label"]} · <span data-i18n="tag.{tagk}">专题</span></span>\n'
            f'  <span class="tt" data-i18n="{m["key"]}.t">…</span>\n'
            f'  <span class="ds" data-i18n="{m["key"]}.d">…</span>\n'
            f'</a>')


def _group_html(gid: str, cards: list[dict]) -> str:
    gkey = dict((g[0], g[1]) for g in DOC_GROUPS)[gid]
    cards_html = "".join(_dcard_html(m) for m in cards)
    return (f'<div class="doc-group" data-proto-id="docs-group-{gid}">\n'
            f'  <h3><span data-i18n="{gkey}">…</span><span class="cnt">{len(cards)}</span></h3>\n'
            f'  <div class="doc-grid">{cards_html}</div>\n'
            f'</div>')


def _scan_json_object(text: str, start: int) -> int:
    """返回与 text[start]（'{'）配对的闭 '}' 下标（跳过字符串字面量）。"""
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    raise BuildError("render", "PROTO_I18N 字典未闭合（真相源漂移）")


def update_i18n_docs(html: str, metas: list[dict]) -> str:
    marker = "window.PROTO_I18N = "
    pos = html.find(marker)
    if pos < 0:
        raise BuildError("render", "docs.html 缺少 PROTO_I18N 字典")
    start = html.index("{", pos + len(marker))
    end = _scan_json_object(html, start)
    i18n = json.loads(html[start:end + 1])
    fresh = {m["key"] + s for m in metas for s in (".t", ".d")}
    for lang in ("zh", "en"):
        pack = i18n.get(lang)
        if not isinstance(pack, dict):
            raise BuildError("render", f"PROTO_I18N 缺少 {lang} 字典")
        # 先删失效文档键（集合变化），再原位更新/追加（保持既有键序，diff 最小）
        for key in [k for k in pack if DOC_KEY_RE.match(k) and k not in fresh]:
            del pack[key]
        for m in metas:
            pack[m["key"] + ".t"] = m["title"]
            pack[m["key"] + ".d"] = m["digest"]
    return html[:start] + json.dumps(i18n, ensure_ascii=False) + html[end + 1:]


def rebuild_doc_groups(html: str, metas: list[dict]) -> str:
    assignment = assign_groups(metas)
    def _repl(m: "re.Match[str]") -> str:
        gid = m.group(1)
        if gid not in assignment:
            raise BuildError("render", f"未知文档分组 docs-group-{gid}")
        return _group_html(gid, assignment[gid])
    html, n = re.subn(r'<div class="doc-group" data-proto-id="docs-group-([a-z-]+)">.*?</div>\n</div>',
                      _repl, html, flags=re.S)
    if n != len(DOC_GROUPS):
        raise BuildError("render", f"docs.html 文档分组区块匹配 {n} 处（预期 {len(DOC_GROUPS)}）")
    return html


def render_docs(tmp: Path) -> list[dict]:
    sync_clone()
    help_src = CACHE / "docs" / "help"
    if not help_src.is_dir():
        raise BuildError("clone", f"源仓库缺少 docs/help/（{help_src}）")
    metas = build_doc_metas(help_src)
    known_stems = frozenset(m["href"][:-5] for m in metas)  # help 集内 stem（.html 去后缀）
    for md in sorted(help_src.glob("*.md")):
        (tmp / "help" / (md.stem + ".html")).write_text(
            md_to_html(md, md.name, known_stems), encoding="utf-8")
    docs_file = tmp / "docs.html"
    html = docs_file.read_text(encoding="utf-8")
    html = update_i18n_docs(html, metas)
    html = rebuild_doc_groups(html, metas)
    docs_file.write_text(html, encoding="utf-8")
    return metas


# ============================================================ 5. inject_gh_data
def fmt_num(v: int) -> str:
    """原型口径：>=1000 显示 x.xk，其余原值。"""
    return f"{v / 1000:.1f}k" if v >= 1000 else str(v)


def fetch_gh_counts() -> tuple[list[str], str | None]:
    req = urllib.request.Request(GH_API_URL, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fenixd-website-build",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return ([fmt_num(data["stargazers_count"]), fmt_num(data["forks_count"]),
                 fmt_num(data["open_issues_count"])], None)
    except Exception as exc:  # 网络/限速/非 200 一律降级，不中断构建
        return ["--", "--", "--"], str(exc)


def inject_gh_data(html: str) -> str:
    marker = '<div class="gh-stats" data-proto-id="comm-gh-stats">'
    start = html.find(marker)
    if start < 0:
        raise BuildError("inject", "community.html 缺少 comm-gh-stats 容器（真相源漂移）")
    end = html.find("\n        </div>", start)
    if end < 0:
        raise BuildError("inject", "comm-gh-stats 容器闭合定位失败")
    window = html[start:end]
    vals, warn = fetch_gh_counts()
    if warn:
        print(f"[WARN] GitHub API 不可达（{warn}），社区数据卡注入 -- 占位，构建继续", file=sys.stderr)
    state = {"i": 0}

    def _repl(m: "re.Match[str]") -> str:
        state["i"] += 1
        if state["i"] <= 3:
            return m.group(1) + vals[state["i"] - 1] + m.group(3)
        return m.group(0)  # 第 4 格为语言静态值（Python），不动

    window = re.sub(r'(<div class="v num">)([^<]*)(</div>)', _repl, window)
    if state["i"] < 4:
        raise BuildError("inject", f"comm-gh-stats 容器内仅 {state['i']} 处数据格（预期 4）")
    return html[:start] + window + html[end:]


# ============================================================ 6. verify + smoke
REF_RE = re.compile(r'(?:src|href)="([^"]+)"')


def verify(dist: Path, n_help_expected: int) -> None:
    pages = sorted(dist.glob("*.html"))
    helps = sorted((dist / "help").glob("*.html"))
    problems: list[str] = []
    if len(pages) != len(PAGES):
        problems.append(f"一级页数量 {len(pages)}（预期 {len(PAGES)}）")
    if len(helps) != n_help_expected:
        problems.append(f"help 页数量 {len(helps)}（预期 {n_help_expected}，与源文档数一致）")
    for page in pages + helps:
        text = page.read_text(encoding="utf-8")
        for ref in REF_RE.findall(text):
            if ref.startswith(("http://", "https://", "mailto:", "data:", "#")):
                continue
            target = ref.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            if not (page.parent / target).exists():
                problems.append(f"{page.relative_to(dist)} -> {ref}")
    if (dist / "annotator.js").exists():
        problems.append("annotator.js 不应出现在产物中")
    if problems:
        raise BuildError("verify", "产物完整性校验失败:\n  " + "\n  ".join(problems[:30]))


def smoke(dist: Path) -> None:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1",
         "--directory", str(dist)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    try:
        ready = False
        for _ in range(25):
            try:
                urllib.request.urlopen(base + "/index.html", timeout=1.5).read(64)
                ready = True
                break
            except Exception:
                time.sleep(0.2)
        if not ready:
            raise BuildError("smoke", "本地 http.server 未就绪")
        help_pages = sorted(p.name for p in (dist / "help").glob("*.html"))[:3]
        must_200 = ([f"/{p}" for p in PAGES]
                    + [f"/help/{h}" for h in help_pages]
                    + ["/logo-64.png", "/mermaid.min.js", f"/assets/{EXPECTED_ASSETS[0]}"])
        for path in must_200:
            try:
                code = urllib.request.urlopen(base + path, timeout=5).status
            except Exception as exc:
                raise BuildError("smoke", f"{path} 探测失败: {exc}")
            if code != 200:
                raise BuildError("smoke", f"{path} HTTP {code}（预期 200）")
        try:
            urllib.request.urlopen(base + "/annotator.js", timeout=5)
            raise BuildError("smoke", "annotator.js 不应可访问（净化失败）")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise BuildError("smoke", f"annotator.js HTTP {exc.code}（预期 404）")
        print(f"[build_site] 冒烟通过：五页 + {len(help_pages)} 篇 help 页 200，annotator.js 404")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


# ============================================================ main
def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("[build_site] 1/6 preflight：校验原型真相源与净化标记")
    preflight()

    if TMP.exists():
        shutil.rmtree(TMP)
    print("[build_site] 2/6 stage：复制五页与静态资源到临时产物目录")
    stage(TMP)

    print("[build_site] 3/6 sanitize：净化仿样横幅 / annotator / 配色 dock")
    for name in PAGES:
        path = TMP / name
        path.write_text(sanitize(path.read_text(encoding="utf-8"), name), encoding="utf-8")

    print("[build_site] 4/6 render_docs：同步 fenixd 源仓库并渲染帮助文档")
    metas = render_docs(TMP)
    print(f"[build_site]   渲染 help/{len(metas)} 篇，docs.html 卡片同步 {len(metas)} 篇真实文档")

    print("[build_site] 5/6 inject_gh_data：注入 GitHub 仓库真实数据")
    cfile = TMP / "community.html"
    cfile.write_text(inject_gh_data(cfile.read_text(encoding="utf-8")), encoding="utf-8")

    print("[build_site] 6/6 verify：资源引用完整性 + 本地冒烟")
    verify(TMP, n_help_expected=len(metas))
    if DIST.exists():
        shutil.rmtree(DIST)
    TMP.rename(DIST)  # 全部成功才产出 site/dist，不产残缺站点
    smoke(DIST)

    files = [p for p in DIST.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    print(f"[build_site] 产物清单：site/dist 共 {len(files)} 个文件，{total / 1024:.1f} KB")
    print("[build_site] 构建完成 ✓")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as exc:
        print(f"[build_site] 构建失败 · {exc.step} 步骤：{exc.msg}", file=sys.stderr)
        if TMP.exists():
            shutil.rmtree(TMP, ignore_errors=True)  # 不产出残缺 site/dist
        sys.exit(1)
