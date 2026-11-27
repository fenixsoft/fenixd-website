## Deliverables

<!-- 交付物声明：daemon 按 kind 机械对账。原型真相源已随立项提交入库，实现 Agent 于 worktree 中可读。 -->

```yaml
- path: specs/website-home-primary-pages/prototype/index.html
  kind: new
  note: UI 真相源（五页 HTML、help/ 16 页渲染页、assets/ 6 张、logo-64.png、mermaid.min.js、generator/build_proto.py、shots/ 五页截图）；立项时随本 change 入库，实现阶段只读引用
- path: build_site.py
  kind: new
  note: 站点构建管线（preflight/stage/sanitize/render_docs/inject_gh_data/verify）
- path: scripts/setup_pages.sh
  kind: new
  note: gh 命令一次性环境设置（幂等，未认证明确指引退出）
- path: .github/workflows/deploy-pages.yml
  kind: new
  note: push main 自动构建并发布 GitHub Pages（官方 actions 链）
- path: DESIGN.md
  kind: new
  note: 界面宪法（品红极光 token/版式/叙事/图标/i18n/图表/资产）
- path: .gitignore
  kind: modify
  note: 追加 site/dist/ 与 .site-cache/ 忽略
- path: README.md
  kind: modify
  note: 站点构建与部署说明 + 人工步骤小节（gh auth login → scripts/setup_pages.sh）
- path: .fenix/todo.md
  kind: modify
  note: 登记人工步骤（认证与首次 setup；文件已存在，仅追加条目）
```

## 1. 设计宪法与真相源校验

- [ ] 1.1 创建仓库根 DESIGN.md 界面宪法：品红极光配色 token 表（ember#B8409A/soft#9C2F81/deep#83286B/tint 四级/grad 三停 120deg #0891B2→#8B5CF6 48%→#B8409A/link#0E7490/term 深底#0F172A/radius 16px）、版式规则（一级页标题全文渐变、card-head 图标标题同行、导航六项、全站禁破折号）、叙事宪法（熵增叙事、无出处数字禁令、Harness 中立口径）、图标宪法（lucide 内联 SVG 禁 emoji）、i18n 宪法（data-i18n zh/en 字典成对全覆盖）、图表宪法（mermaid 本地 vendor 渲染）、资产宪法（英文 UI 真实截图）；内容取材 specs/website-home-primary-pages/prototype/generator/build_proto.py 头部注释与实现
- [ ] 1.2 build_site.py 实现 preflight 校验：真相源五页 HTML、help/ 16 页、assets/ 6 张、logo-64.png、mermaid.min.js 全部在位；五页含预期净化标记（proto-banner class、annotator.js 引用、-palette-dock 锚），缺失即非零退出并指明缺件

## 2. 构建管线 build_site.py

- [ ] 2.1 实现 stage 与 sanitize：复制五页+静态资源到 site/dist/（静态资源复制 MUST 排除原型脚手架文件 annotator.js；保留 i18n 引擎与站点交互），移除仿样横幅块（class 含 proto-banner）、annotator.js 的 script 引用（实测形如 `<script src="annotator.js" defer>`，按 src 含 annotator.js 匹配）、配色 dock（data-proto-id 以 -palette-dock 结尾元素及其 localStorage 初始化脚本块）；净化后 grep 断言三标记零残留、语言切换按钮仍在
- [ ] 2.2 实现 render_docs：浅克隆 github.com/fenixsoft/fenixd 至 .site-cache/fenixd（已存在则 git fetch --depth 1 复用），迁移 generator/build_proto.py 的 md_to_html/help_meta 渲染逻辑生成 site/dist/help/*.html，docs.html 文档中心卡片标题/摘要/篇数同步真实文档；克隆失败非零退出
- [ ] 2.3 实现 inject_gh_data：请求 api.github.com/repos/fenixsoft/fenixd，将 stargazers_count/forks_count/open_issues_count 注入 community.html 数据卡三值（原型示例假数据 2.1k/318/47，位于 data-proto-id="comm-gh-stats" 容器内按序前三处 `<div class="v num">`；第 4 格 gh.s4 为语言静态值 Python，MUST NOT 改动），沿用原型 >=1000 显示 x.xk 格式化；API 失败注入 -- 并打印 WARN，构建继续
- [ ] 2.4 实现收尾 verify 与本地冒烟：产物资源引用完整性（img/script/内链 href 目标存在于 dist）；`python3 -m http.server` 起临时服务探测五页+至少 3 篇 help 页 200、净化项 404/不存在；构建末尾打印产物清单（文件数/总大小）

## 3. Pages 部署与一次性设置

- [ ] 3.1 创建 .github/workflows/deploy-pages.yml：on push branches [main] + workflow_dispatch；单 job permissions（pages: write/id-token: write/contents: read）、environment github-pages、并发组取消旧部署；步骤 checkout → setup-python 3.11 → python3 build_site.py → actions/configure-pages → actions/upload-pages-artifact(path: site/dist) → actions/deploy-pages
- [ ] 3.2 创建 scripts/setup_pages.sh（幂等）：gh auth status 未认证则打印「请先运行 gh auth login（一次性人工步骤）」退出 1；gh repo view fenixsoft/fenixd-website 确认仓库；gh api repos/fenixsoft/fenixd-website/pages 404 时 POST 启用 build_type=github-actions（已启用则校验/校正）；输出 Pages 状态与首次部署触发提示；shellcheck 语法通过（bash -n + shellcheck 如可用）
- [ ] 3.3 更新 .gitignore（追加 site/dist/ 与 .site-cache/）与 README.md（站点简介、本地构建 python3 build_site.py + http.server 预览、部署链路说明、「人工步骤」小节：gh auth login → bash scripts/setup_pages.sh）
- [ ] 3.4 在 .fenix/todo.md 追加人工步骤条目：gh auth login 认证（一次性）与执行 scripts/setup_pages.sh 启用 Pages；标注完成判定（Pages URL 五页 200）

## 4. 端到端验收

- [ ] 4.1 全链路构建冒烟：干净环境（删除 site/dist 与 .site-cache）跑 python3 build_site.py 一次成功；产物 diff 原型仅命中净化标记与 comm-gh-stats 容器内动态值（静态内容一致性抽查：五页标题/H1/导航六项/页脚与原型一致）；help 页数与 fenixd docs/help 文档数一致
- [ ] 4.2 交付物自查：Deliverables 八项全部落位且路径准确；QA 产物（构建输出/冒烟记录）留存 .fenix/verify-serving/ 或 tasks 描述内可复现命令
