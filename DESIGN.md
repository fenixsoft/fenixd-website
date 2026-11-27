# DESIGN.md · fenixd-website 界面宪法

本文件沉淀 fenixd 官网（`specs/website-home-primary-pages/prototype/` 为 UI 真相源）20 轮浏览器批注迭代定稿的设计约束。后续任何页面扩展 MUST 遵守本宪法；与原型冲突时以原型为准（冲突升级用户裁决）。取材自原型生成器 `specs/website-home-primary-pages/prototype/generator/build_proto.py` 的头部注释、CSS token 单源与页面实现。

## 1. 配色宪法（品红极光 token）

全站唯一发布配色为 `orchid-aurora`（品红极光），经 `<body data-palette="orchid-aurora">` 固化。原型的配色 dock 是比选脚手架，站点不随发布（构建时净化）。

### 品红主色（ember 四级）

| token | 值 | 用途 |
|---|---|---|
| `--ember` | `#B8409A` | 主品牌色（品红梅）：主按钮、强调、logo |
| `--ember-soft` | `#9C2F81` | hover / 次级强调、正文链接Fallback色 |
| `--ember-deep` | `#83286B` | 深品红：tint 底上的文字、lang-toggle 激活态 |
| `--tint-*` | `#FDF2F8` / `#FCE7F3` / `#FBCFE8` / `#F9A8D4` | 品红淡出四级（bg / soft / line / edge），横幅、徽章、激活底色 |

### 渐变与链接

| token | 值 | 用途 |
|---|---|---|
| `--grad-brand` | `linear-gradient(120deg, #0891B2 0%, #8B5CF6 48%, #B8409A 100%)` | 品牌三停渐变（青→紫→品红），标题渐变文字、导航激活下划线 |
| `--link` | `#0E7490` | 正文链接（青色，唯一允许的蓝色语义） |
| `--focus-ring` | `rgba(184,64,154,.15)` | 聚焦光环 |
| `--glow-a` / `--glow-b` | `rgba(8,145,178,.08)` / `rgba(184,64,154,.07)` | 极光背景辉光（青 / 品红） |
| `--hl-edge` | `rgba(184,64,154,.55)` | 高亮边缘 |
| `--term-ember` | `#E879C8` | 终端块内的品红高亮 |

### 中性底与语义色

| token | 值 | 用途 |
|---|---|---|
| `--bg` / `--card` / `--card-2` | `#FAFAFA` / `#FFFFFF` / `#F4F4F5` | 页面底 / 卡片 / 次级卡片 |
| `--line` / `--line-strong` | `#E5E7EB` / `#D1D5DB` | 分隔线 / 强分隔线 |
| `--text` / `--text-2` / `--text-3` | `#111827` / `#6B7280` / `#9CA3AF` | 正文 / 次级 / 弱化三级灰 |
| `--verified` | `#16A34A` | 绿色，仅用于「已验证」语义 |
| `--danger` / `--warn` | `#DC2626` / `#B45309` | 危险 / 警示 |
| `--term-bg` / `--term-bar` | `#0F172A` / `#0B1220` | 代码块与终端深底 |

蓝色纪律：蓝色只允许 `--link`（`#0E7490`）链接语义与渐变首停 `#0891B2`，不得回归大面积蓝紫渐变；绿色只允许「已验证」语义。圆角 `--radius: 16px`（卡片级）/ 9px（按钮级）；版心 `--maxw: 1200px`；页头高 `--header-h: 64px`。

## 2. 版式规则

- **一级页标题全文渐变**：五个一级页（index/why/capabilities/docs/community）的 H1 均含 `<span class="grad-text">` 渐变文字（应用 `--grad-brand`）；index 页为首屏 H1 的副题半句渐变，其余四页为标题全文渐变。
- **card-head 图标标题同行**：卡片头部为「图标（`card-ic`）+ 标题」水平同行排布，图标用 `icon()` 内联 SVG。
- **导航六项**：全站导航固定六项（首页 / 快速开始 / 使用场景 / 能力全景 / 文档 / 社区）+ 右侧语言切换与 GitHub 按钮；移动端折叠为 burger 菜单。
- **全站禁破折号**：中文语境不使用「——」长破折号，一律以逗号 / 顿号重构句子。文案、i18n 字典、文档渲染均适用。
- 单文件自包含：每页 CSS 内联于 `<style>`，无外部样式表与字体依赖；正文 16px / 行高 1.65，标题字重 700-800。
- 减动效纪律：`prefers-reduced-motion` 下关闭全部 animation / transition 与平滑滚动。

## 3. 叙事宪法（熵增叙事）

- **熵增叙事主线**：AI 让写代码快十倍，也让软件熵增快十倍；Fenixd 用四类机制对抗熵增（SPEC 驱动、循环验证、质量门禁、知识蒸馏），把约束从口头指南升级为机器执行的硬闸门。why 页承载六失控点 + 机制映射表 + story 叙事区。
- **无出处数字禁令**：页面出现的每一个数字 MUST 有出处（真实仓库 API、真实文档、仓库运转口径），无出处的示例数字在正式站中 MUST 被动态注入替换（如社区页 stars/forks/issues）或明确标注「示例」。
- **Harness 中立品牌口径**：Fenixd 是 Harness 中立的自动化软件开发循环框架，表述为「支持 Claude Code、DSH 等」，不得绑定单一 Harness 品牌。
- 数据出处口径：仓库运转数字来自 fenixd 自身仓库（dogfooding），文档数字来自 `docs/help/` 真实篇数，社区数据来自 GitHub API 构建时注入。

## 4. 图标宪法（lucide 内联 SVG）

- 全站图标为 lucide 语义图标，24×24 viewBox、`fill="none" stroke="currentColor"`、stroke-width 1.8，经 `icon()` 以内联 `<svg>` 嵌入页面。
- **禁 emoji**：任何 UI 位置不得使用 emoji 充当图标（i18n 字典摘要生成时亦剥离 emoji 区段）。

## 5. i18n 宪法（data-i18n 全键覆盖）

- 中英双语：页面内嵌 `window.PROTO_I18N = {"zh": {...}, "en": {...}}` 单字典，元素经 `data-i18n`（innerHTML）/ `data-i18n-ph`（placeholder）/ `data-i18n-title` / `data-i18n-label` 挂钩。
- **zh/en 字典成对全覆盖**：每个键 zh/en 必须成对出现，缺失即键漂移；含终端/代码文案（term 行）在内的全部用户可见文案都纳入字典。
- 语言状态记忆于 `localStorage('fenixd-proto-lang')`，默认 zh；语言切换按钮（`#lang-zh` / `#lang-en`）为站点交互，构建净化时 MUST 保留。

## 6. 图表宪法（mermaid 本地 vendor 渲染）

- 文档页 mermaid 图表经本地 `mermaid.min.js` 图形化渲染（不依赖外网 CDN）：`mermaid.initialize({startOnLoad:false, theme:"neutral", securityLevel:"strict"})` 后 `mermaid.run({querySelector:"pre.mermaid"})`。
- 渲染源码以 `<pre class="mermaid">` 原文保留；渲染失败时容器降级为 `.mm-err` 文本展示，不得静默丢图。

## 7. 资产宪法（真实截图，英文 UI）

- Dashboard 配图 MUST 使用真实产品截图（`assets/dash-*.png` 六张），界面为英文 UI；不得用手绘示意图或占位图替代。
- `logo-64.png` 为全站 favicon 与页头 logo 位；截图配图经灯箱（lightbox）交互放大查看。
