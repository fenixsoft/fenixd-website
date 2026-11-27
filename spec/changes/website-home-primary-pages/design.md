## Context

原型已定稿并入库为 UI 真相源（`specs/website-home-primary-pages/prototype/`）。本设计回答：如何把原型转为可部署站点、动态化如何做、Pages 如何自动部署、环境设置如何经 gh 完成。

## Goals

- 静态内容与原型严格一致（用户硬约束：把 HTML 复制过去，仅动态点修改）
- 构建产物零依赖纯静态；构建脚本标准库实现
- push main → GitHub Pages 自动更新

## Non-Goals

- 不重做 UI、不引入框架/打包器、不做自定义域名与 CDN、不做站点搜索与 SSR

## Decisions

### D1 站点形态：纯静态 HTML/CSS/JS，无框架
原型即零依赖静态页（CSS 内联单文件、icon() 内联 SVG）。正式站点延续该形态：`build_site.py` 复制原型 HTML 为起点做后处理，不重写页面。备选「用框架重写」被否——与「严格按原型实现」硬约束冲突且无收益。

### D2 构建管线：单脚本 `build_site.py`（标准库）
流程：`preflight`（校验真相源五页齐全）→ `stage`（五页+静态资源复制到 `site/dist/`）→ `sanitize`（移除仿样横幅/annotator script/配色 dock/原型 meta）→ `render_docs`（见 D3）→ `inject_gh_data`（见 D4）→ `verify`（锚点/资源引用完整性冒烟）→ 输出产物清单。原型脚手架的识别锚：`proto-banner` class、`annotator.js` 引用、`-palette-dock` 后缀 data-proto-id、`STYLE-SWITCHER` 注释块。净化规则以原型 HTML 中的显式标记为准（原型生成器已在这些块上加注释，见 tasks T3 校验）。

### D3 文档动态化：构建时浅克隆 fenixd + 迁移渲染管线
`git clone --depth 1 https://github.com/fenixsoft/fenixd`（优先复用本地缓存 `.site-cache/fenixd`，`git fetch` 刷新）→ 读 `docs/help/*.md` → 用原型生成器 `generator/build_proto.py` 的 `md_to_html()`/`help_meta()` 逻辑（迁移复制进 build_site.py，行为不变）渲染 16+ 篇 `help/*.html` + 更新 docs.html 卡片标题/摘要/篇数。克隆失败 → 构建失败非零退出（需求 Scenario）。不在运行时经 JS 拉文档（无后端且 CORS 不可控）。

### D4 GitHub 数据动态化：构建时公共 API 注入
`GET api.github.com/repos/fenixsoft/fenixd`（本地构建无 token；workflow 内 Actions 自动注入 GITHUB_TOKEN 供 pages 部署，API 读取无需认证）→ 取 `stargazers_count`/`forks_count`/`open_issues_count` → 替换 community 页数据卡三值（原型示例假数据 2.1k/318/47）。HTML 中三值有唯一可定位包装（原型 data-proto-id `comm-stat-*`），正则/BeautifulSoup-free 字符串替换即可。失败降级 `--` + WARN（需求 Scenario）。数字格式化沿用原型函数（>=1000 显示 x.xk）。

### D5 Pages 部署：官方 Actions 链
`.github/workflows/deploy-pages.yml`：`on: push: branches: [main]` + `workflow_dispatch`；单 job `permissions: pages: write, id-token: write, contents: read`；环境 `github-pages`；并发组 `pages-${{ github.ref }}` cancel-in-progress；步骤=checkout → setup-python 3.11 → `python3 build_site.py` → actions/configure-pages → actions/upload-pages-artifact(path=site/dist) → actions/deploy-pages。Pages 源必须是 github-actions 构建模式（D6 脚本启用），非「deploy from branch」。

### D6 一次性环境设置：`scripts/setup_pages.sh`（gh 封装，幂等）
步骤：① `gh auth status` 未认证则打印「请先运行 gh auth login（一次性人工步骤）」退出 1；② `gh repo view fenixsoft/fenixd-website` 确认仓库；③ Pages 启用/校验：`gh api repos/fenixsoft/fenixd-website/pages` 404 时 `gh api -X POST .../pages -f build_type=github-actions`，已启用且 build_type 非 github-actions 时 `gh api -X PUT ... 改`；④ 校验 workflow 权限设置（`gh api repos/.../actions/permissions/workflow` default_workflow_repository_permissions）。认证无法由 Agent 代做（交互式），列为人工步骤：README「人工步骤」小节 + `.fenix/todo.md` 登记。

### D7 `DESIGN.md` 界面宪法（随本 SPEC 创建于仓库根）
沉淀 20 轮迭代定稿的设计约束，供后续页面扩展遵守：品红极光配色 token（ember#B8409A/soft#9C2F81/deep#83286B/tint#FDF2F8/#FCE7F3/#FBCFE8/#F9A8D4/grad 三停 120deg #0891B2→#8B5CF6 48%→#B8409A/link#0E7490/verified#16A34A/danger#DC2626/term 深底#0F172A/radius 16px）、版式规则（一级页标题全文渐变 span.grad-text、card-head 图标标题同行、导航六项、全站禁破折号——中文语境用逗号重构）、叙事宪法（熵增叙事：每断言有出处，无出处数字禁令；六失控点+映射表+story 区；Harness 中立品牌口径）、图标宪法（lucide 语义图标 24x24 stroke 内联，禁 emoji）、i18n 宪法（data-i18n 全键覆盖含 term 行，zh/en 字典成对）、图表宪法（mermaid 本地 vendor 图形渲染）、资产宪法（dashboard 真实截图英文 UI）。

## Risks / Trade-offs

- [构建时克隆 fenixd 使构建依赖外网] → 缓存复用 + 失败显式退出（不静默出残缺站点）
- [公共 API 匿名限速 60/h] → 单次构建仅 1 次调用；workflow 内频率天然低
- [Pages 首次部署需 Pages 已启用] → setup_pages.sh 前置人工步骤 + workflow 内 configure-pages 自带校验
- [原型 HTML 与站点 HTML 漂移] → DESIGN.md 宪法 + 需求「构建管线以原型为界面真相源」约束后处理白名单

## Migration Plan

全新站点，无存量迁移。上线后原 404 的 fenixsoft.github.io/fenixd-website 变为官网入口。

## Open Questions

- 无（自定义域名、监控等留待后续 SPEC）
