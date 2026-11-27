# 验证报告：website-home-primary-pages

> ⚠️ 本报告由框架于 2026-11-27T05:08:25Z 自动合成（裁决 Agent 未写报告，已由框架合成），内容为结构化验证产物（report.json / .fenix-run-result.json）的忠实渲染。
> 报告时效标记（判定本报告是否属上一轮）：合成源轮次指纹：report.json@2026-11-27T05:08:25.457299+00:00+run-result@mtime1795756105703644063

## 结论：✅ 通过（verified）

**状态：verified — 22/22 场景通过，0 失败，0 错误（全部场景通过）**

全绿快道: 22/22 场景通过、0 失败 0 警告——无分类对象，跳过 judge 机械 verified

| 指标 | 数量 |
| --- | --- |
| 通过 | 22 |
| 失败 | 0 |
| 错误 | 0 |
| 产品 Bug | 0 |
| 本链增量 Token（输入） | 7.52M |
| 本链增量 Token（输出） | 0.17M |


## 场景结果

| 场景 | 描述 | 状态 | 失败断言 | 分类 |
| --- | --- | --- | --- | --- |
| build-clean-full-run | 干净环境全链路构建：删除 site/dist 与 .site-cache 后执行 python3 build_site.py 一次成功；产物五页/help 渲染页/静态资源齐全，help 页数与源仓库 docs/help 文档数一致；仿样横幅（proto-banner）、annotator.js 引用与文件、配色 dock（-palette-dock）三净化标记零残留，语言切换/移动导航/汉堡按钮站点交互元素保留（出处：spec.md「从原型构建站点」、tasks 2.1-2.4 与 4.1；净化锚原型实测 index.html:787 annotator.js 引用、各页 -palette-dock 与 proto-banner） | pass | 0/20 | - |
| pages-live-deployed | 【环境依赖】【无 fallback】GitHub Pages 线上部署验收：五页经 https://fenixsoft.github.io/fenixd-website/ 全 200。依赖一次性人工步骤（gh auth login、bash scripts/setup_pages.sh 启用 Pages、push main 触发 Actions 部署），验证环境无法代做交互式认证与云端部署链；未部署时本场景如实失败，由框架按环境阻塞处置（出处：spec.md「push main 自动部署」「部署产物完整性」、design.md D5/D6） | pass | 0/5 | - |
| gh-data-inject-real-values | GitHub 数据真实注入：构建产物 community.html 的 comm-gh-stats 容器前三格与 api.github.com/repos/fenixsoft/fenixd 当时的真实 stars/forks/open_issues 一致（解析容差覆盖 x.xk 格式化），容器内第 4 格语言静态值 Python 未被注入改动（出处：spec.md「真实仓库数据注入」、design.md D4；原型 community.html:506-510 四格结构实测） | pass | 0/2 | - |
| build-preflight-failure-gate | preflight 失败门：临时移走原型真相源 index.html 后构建以非零码失败且错误指明缺件（index.html/preflight），既有 site/dist 不被污染（preflight 先于 stage）；随后恢复真相源并校验在位（出处：tasks 1.2 preflight 校验五页在位、design.md D2 流程序） | pass | 0/5 | - |
| build-clone-failure-nonzero | 源仓库不可达构建失败：清空缓存与产物后以 GIT_CONFIG_COUNT insteadOf 将源仓库 URL 重写至不可达端点阻断 git clone（代理环境变量方案失效：本机 git 全局 http.https://github.com/.proxy 配置优先于环境变量使 clone 仍可达，2026-11-27 裁决实测），构建以非零码退出且错误信息指明失败的子步骤（clone/源仓库/render），不产出残缺 site/dist/help；随后无重写正常重建恢复完整产物（出处：spec.md「源仓库不可达时构建失败并给出明确报错」、design.md D3） | pass | 0/5 | - |
| build-gh-api-degrade-placeholder | GitHub API 失败降级：以坏代理阻断 api.github.com（git 经空 http.proxy 配置覆写保持 clone 可达；no_proxy=127.0.0.1,localhost 豁免 loopback——代理 env 是全局毒化，缺豁免会把 build_site.py smoke 对本地 http.server 的 urlopen 也路由进死代理致「未就绪」误判，2026-11-27 裁决场景修复，复现实测占位 3 处且构建完成）执行构建，构建不失败且输出 WARN 警告日志，community.html 数据卡前三格注入 -- 显式占位（各 1 处共 3 处）、第 4 格 Python 静态值不变（出处：spec.md「API 失败降级」、design.md D4） | pass | 0/5 | - |
| dist-local-http-smoke | 构建产物本地伺服冒烟：动态端口起 http.server 伺服 site/dist，五页+3 篇 help 页+mermaid.min.js+dashboard 截图+logo 全部 200，净化文件 annotator.js 经 HTTP 不可达（404）（出处：tasks 2.4 收尾 verify 与本地冒烟；spec.md「部署产物完整性」的本地等价物） | pass | 0/12 | - |
| workflow-yml-deploy-chain | Pages 部署 workflow 静态契约：.github/workflows/deploy-pages.yml 存在且含 push main 触发、workflow_dispatch、python3 build_site.py 构建命令、官方 Actions 三链（configure-pages/upload-pages-artifact/deploy-pages）、site/dist 上传路径、pages: write 与 id-token: write 权限、github-pages 环境与并发组（出处：spec.md「GitHub Actions 自动部署 Pages」、design.md D5、tasks 3.1） | pass | 0/13 | - |
| setup-pages-unauth-gate | 未认证环境明确指引：以无效 GH_TOKEN 强制 gh auth status 失败（本机已认证环境下的确定性未认证模拟）后执行 scripts/setup_pages.sh，脚本输出 gh auth login 指引并以非零码退出，走无副作用路径不触达远端（出处：spec.md「未认证环境明确指引」、design.md D6、tasks 3.2） | pass | 0/2 | - |
| setup-pages-syntax-and-content | setup_pages.sh 语法与关键段静态校验：bash -n 语法通过（shellcheck 如可用则 -S error 通过）；脚本含 gh auth status 认证门、fenixsoft/fenixd-website 仓库确认、gh api 启用 Pages（build_type=github-actions）与「未启用即启用 / 已启用幂等跳过」幂等分支（脚本以 gh api 探测空值分支实现 404 幂等、全文无字面量 404，断言按实际机制校验且强度不降——2026-11-27 裁决修正）（出处：design.md D6、tasks 3.2；已认证一键设置路径因会产生真实远端副作用不实跑，由内容断言覆盖） | pass | 0/8 | - |
| site-docs-gitignore-todo-readme | 配套文档交付：.gitignore 追加 site/dist/ 与 .site-cache/ 忽略；README 含本地构建（build_site.py）、http.server 预览与「人工步骤」小节（gh auth login、setup_pages.sh）；.fenix/todo.md 登记人工步骤条目（出处：tasks 3.3、3.4、proposal Impact） | pass | 0/12 | - |
| design-md-constitution | DESIGN.md 界面宪法落位：品红极光配色 token（ember #B8409A、grad 三停 #0891B2/#8B5CF6、term 深底 #0F172A、radius 16px）、lucide 图标宪法、data-i18n 字典宪法、mermaid 本地渲染宪法、grad-text 版式与全站禁破折号规则成文（出处：design.md D7、tasks 1.1） | pass | 0/11 | - |
| web-index-render-sanitized | 首页渲染与净化（navigate http://127.0.0.1:8787/index.html，origin 由引擎按验证实例改写、路径 /index.html 来自原型站点结构）：hero 标题（缺省 zh）与导航项可见，仿样横幅/annotator 引用/配色 dock 零残留，控制台与网络零错误（出处：spec.md「从原型构建站点」「站点交互与原型一致」；锚点原型实测 index.html:472 lang-toggle、:482 mobile-nav、:787 annotator.js 引用） | pass | 0/8 | - |
| web-lang-toggle-en-persist | 中英切换与记忆（navigate http://127.0.0.1:8787/index.html）：点击 EN 后导航首项变 Home、hero 出现英文文案且 EN 按钮激活，重载同页后英文保持（localStorage 记忆链路）（出处：spec.md「站点交互与原型一致」；锚点 index.html:472-474 #lang-zh/#lang-en、i18n 字典 nav.home en=Home、hero.h1 en 含 software development） | pass | 0/5 | - |
| web-quickstart-anchor-jump | 锚点跳转（navigate http://127.0.0.1:8787/index.html）：点击桌面导航「快速开始」后 quickstart 区块滚入视口；点击后 wait 800ms 待平滑滚动动画完成再评估（原型 index.html:26 html{scroll-behavior:smooth}）；in_viewport 目标为区块标题 #quickstart h2——#quickstart 整块（原型 index.html:572-610，含 3 张 card-shot）渲染高度超 800px 视口，引擎全包含口径（rect.bottom≤innerHeight）下对整块断言机械不可满足（2026-11-27 裁决目标修正：滚动未发生时 h2 同样不入视口，检测强度不降；wait 800ms 时序修复保留）（出处：spec.md「站点交互与原型一致」锚点跳转；锚点 index.html:465 导航链接 href=index.html#quickstart、:572 section id=quickstart） | pass | 0/4 | - |
| web-mobile-nav-toggle | 移动端菜单（navigate http://127.0.0.1:8787/index.html，声明 390×844 视口触发 920px 断点）：点击汉堡按钮后移动导航展开、菜单内链接可见且 aria-expanded 置 true（出处：spec.md「站点交互与原型一致」移动端菜单；锚点 index.html:478 #nav-burger、:482 #mobile-nav、:381 .mobile-nav.open 显示规则） | pass | 0/5 | - |
| web-docs-center-cards | 文档中心卡片（navigate http://127.0.0.1:8787/docs.html）：16 张文档卡片（a.doc-card）在位且首卡可见，卡片标题/摘要经构建时动态渲染取自真实文档（出处：spec.md「文档内容随源仓库更新」、tasks 2.2；docs.html doc-card 结构实测，动态篇数与源仓库一致性由 cli 场景 build-clean-full-run 的 HELP_COUNT 对账承担） | pass | 0/5 | - |
| web-help-render-from-card | help 渲染页点击直达（navigate http://127.0.0.1:8787/docs.html 后点击快速上手卡片进入 help/01-quick-start.html）：页面含来源标注「本页由 Fenixd 仓库 docs/help/01-quick-start.md 渲染生成」与本地 vendor mermaid.min.js 引用（出处：spec.md「文档内容随源仓库更新」渲染配置、design.md D3；来源标注格式 build_proto.py:151 实测） | pass | 0/5 | - |
| web-community-gh-card | 社区页数据卡（navigate http://127.0.0.1:8787/community.html）：comm-gh-stats 容器与语言静态格（Python）渲染可见，净化项零残留；动态注入值正确性由 cli 场景 gh-data-inject-real-values 与 build-gh-api-degrade-placeholder 承担（出处：spec.md「真实仓库数据注入」；锚点 community.html:506-510 四格结构实测） | pass | 0/7 | - |
| web-why-page-render | why 页渲染与净化（navigate http://127.0.0.1:8787/why.html）：hero 标题（zh「为什么是 Fenixd」渐变）可见，仿样横幅/annotator/配色 dock 零残留，零控制台/网络错误（出处：spec.md「从原型构建站点」五页产物；why.html 原型实测净化锚与 hero.h1 字典） | pass | 0/7 | - |
| web-capabilities-page-render | capabilities 页渲染与净化（navigate http://127.0.0.1:8787/capabilities.html）：hero 标题（zh「能力全景」渐变）可见，三净化标记零残留，零控制台/网络错误（出处：spec.md「从原型构建站点」五页产物；capabilities.html 原型实测净化锚与 hero.h1 字典） | pass | 0/7 | - |
| web-lightbox-open-close | 图片灯箱开合（navigate http://127.0.0.1:8787/index.html）：点击截图卡打开灯箱展示对应 dashboard 截图，点击遮罩关闭，再点第二张截图卡灯箱以新图重开；链式断言使「开」与「关」缺陷各自机械暴露（出处：spec.md「站点交互与原型一致」图片灯箱；锚点 index.html:596-605 三张 card-shot、:772-783 .lb 动态创建与 ESC/点击关闭逻辑） | pass | 0/3 | - |

## 本轮场景集变更

场景集与持久化集一致，无变更。

