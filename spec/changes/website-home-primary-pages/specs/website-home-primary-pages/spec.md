## ADDED Requirements

> 界面原型（UI 真相源）：`specs/website-home-primary-pages/prototype/`（品红极光配色、中英双语、20 轮批注定稿；含五页 HTML、help 渲染页、dashboard 截图、整页截图与原型生成器 `generator/build_proto.py`）。
> 界面以 prototype/ 为准（冲突须升级用户裁决）；本 SPEC 各 Scenario 的数值口径仅约束动态注入逻辑。
> 设计约束以仓库根 `DESIGN.md` 为准；本 SPEC 交付同时创建 DESIGN.md 界面宪法（见 design.md 决策 D7）。

### Requirement: 站点构建管线以原型为界面真相源
构建脚本 `build_site.py` MUST 以 `specs/website-home-primary-pages/prototype/` 下的五页 HTML（index/why/capabilities/docs/community）为唯一界面来源复制生成正式站点；静态内容（文案、布局、图标、交互脚本）MUST 原样保留。构建后处理仅限三类：原型脚手架净化、help 文档动态渲染、GitHub 数据动态注入（见各自 Requirement）。构建产物 MUST 为零外部依赖的纯静态文件（HTML/CSS/JS 直接伺服，无框架、无运行时构建）。

#### Scenario: 从原型构建站点
- **WHEN** 在仓库根执行 `python3 build_site.py`（工作区存在 prototype/ 真相源）
- **THEN** `site/dist/` 生成五页 HTML 与全部静态资源（logo、dashboard 截图、CSS 内联不变）；除本 SPEC 声明的净化与动态注入点外，HTML 内容与原型逐字节一致（diff 仅命中净化标记与动态占位段）
- **THEN** 净化项全部移除：仿样横幅（class 含 proto-banner）、annotator.js 的 script 引用（实测形如 `<script src="annotator.js" defer>`，按 src 含 annotator.js 匹配）且 annotator.js 文件不出现在产物中、配色 dock（data-proto-id 以 `-palette-dock` 结尾的元素及其 localStorage 脚本）；语言切换、移动端导航等站点交互完整保留

#### Scenario: 站点交互与原型一致
- **WHEN** 浏览器打开构建产物任一页面
- **THEN** 中英切换（zh/en 全量替换、localStorage 记忆）、移动端菜单、锚点跳转、图片灯箱与原型行为一致；页面无 annotator 面板、无仿样横幅、无配色 dock

### Requirement: help 文档构建时从 fenixd 源仓库动态渲染
文档中心（docs.html）的 16 篇 help 文档页 MUST 在构建时从 `fenixsoft/fenixd` 仓库的 `docs/help/*.md` 动态生成：clone（浅克隆）源仓库 → 用原型自带的渲染管线（`generator/build_proto.py` 的 `md_to_html`/`help_meta` 逻辑迁移至 `build_site.py`）渲染为自包含 HTML → 文档中心卡片的标题与摘要取自真实文档首段。渲染配置 MUST 与原型一致（mermaid 图表经本地 vendor `mermaid.min.js` 图形化渲染、代码块深底、表格斑马线、来源标注「本页由 Fenixd 仓库 docs/help/xxx.md 渲染生成」）。

#### Scenario: 文档内容随源仓库更新
- **WHEN** fenixd 仓库 `docs/help/` 新增或修改一篇 markdown 后重新执行构建
- **THEN** 构建产物 `site/dist/help/` 包含该文档的渲染页（新增文档篇数变化时文档中心卡片同步增减）；卡片标题/摘要与文档真实 `#` 标题、首段一致

#### Scenario: 源仓库不可达时构建失败并给出明确报错
- **WHEN** 构建机无法 clone fenixd 仓库（网络不可达）
- **THEN** build_site.py 以非零退出码失败，错误信息指明失败的子步骤（clone/render），不产出残缺的 site/dist

### Requirement: GitHub 仓库数据构建时动态注入
社区页（community.html）的仓库数据卡（stars/forks/open issues）MUST 在构建时经 GitHub 公共 API（`api.github.com/repos/fenixsoft/fenixd`）取真实值注入，替换原型的示例假数据（2.1k/318/47）；数字格式化与卡片版式保持原型样式。API 失败时构建 MUST NOT 静默使用假数据：以显式占位（如 `--`）注入并在构建输出警告。

#### Scenario: 真实仓库数据注入
- **WHEN** 构建执行且 api.github.com 可达
- **THEN** community 页数据卡显示 fenixsoft/fenixd 当时的真实 stars/forks/open_issues 值（与 API 响应一致）

#### Scenario: API 失败降级
- **WHEN** 构建时 GitHub API 不可达或返回非 200
- **THEN** 数据卡注入 `--` 占位且构建输出 WARN 日志，构建不失败、其余产物正常生成

### Requirement: GitHub Actions 自动部署 Pages
仓库 MUST 包含 `.github/workflows/deploy-pages.yml`：push 到 main 触发，跑 `python3 build_site.py` 后经官方 Actions 链（actions/configure-pages、actions/upload-pages-artifact、actions/deploy-pages）把 `site/dist/` 发布到 GitHub Pages。workflow MUST 授予 `pages: write` 与 `id-token: write` 权限，并发组取消旧部署。

#### Scenario: push main 自动部署
- **WHEN** 一次性环境设置已完成（GitHub Pages 已启用，见 Requirement「一次性环境设置经 gh 命令完成」），且五页或构建脚本变更合入 main
- **THEN** workflow 自动构建并部署，站点在 `https://fenixsoft.github.io/fenixd-website/` 可访问（五页 + help 渲染页全 200，内容为最新构建产物）

#### Scenario: 部署产物完整性
- **WHEN** 部署完成
- **THEN** 五页、`help/*.html`、`mermaid.min.js`、`assets/*.png`、`logo-64.png` 全部经 Pages URL 可达（HTTP 200）

### Requirement: 一次性环境设置经 gh 命令完成
仓库 MUST 提供 `scripts/setup_pages.sh`（gh 命令封装，幂等可重跑）：校验 `gh auth status` 已认证 → 确认远端仓库 `fenixsoft/fenixd-website` 存在 → 经 `gh api` 启用 GitHub Pages（build_type=github-actions）→ 校验 workflow 默认权限允许部署。认证本身（`gh auth login`）是一次性人工步骤：脚本检测到未认证时 MUST 输出明确指引后退出（不尝试代做认证）；人工步骤同时登记于 README「人工步骤」小节与 `.fenix/todo.md`。

#### Scenario: 已认证环境一键设置
- **WHEN** 在已 `gh auth login` 的环境执行 `bash scripts/setup_pages.sh`
- **THEN** Pages 以 github-actions 构建源启用（重复执行幂等成功），脚本输出 Pages 状态与首次部署触发提示

#### Scenario: 未认证环境明确指引
- **WHEN** 在未认证环境执行脚本
- **THEN** 脚本提示「请先 gh auth login」并以非零码退出，不产生任何副作用
