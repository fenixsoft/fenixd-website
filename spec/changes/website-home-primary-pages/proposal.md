## Why

fenixd 需要一个对外官网（参考 spring.io 的信息结构），向访客讲清「Fenixd 解决什么问题、如何工作、如何上手」。官网 UI 已经过 20 轮浏览器批注迭代并于会话内定稿（品红极光配色、中英双语、熵增叙事），原型已按 fenix-prototype §6 批准入库为 UI 真相源（`specs/website-home-primary-pages/prototype/`）。本 SPEC 把定稿原型转为可部署的正式站点，并经 GitHub Actions 自动发布到 GitHub Pages。

## What Changes

- 新增站点构建管线 `build_site.py`：以入库原型 HTML 为唯一界面来源（静态内容原样复制），仅做三类后处理——
  1. **净化**：移除仿样横幅、annotator.js 引用、配色 dock 等原型脚手架（站点内容与交互不改动）；
  2. **文档动态化**：构建时 clone `fenixsoft/fenixd` 仓库，取 `docs/help/*.md` 用原型自带的渲染管线（`md_to_html` / `help_meta`）生成 `help/*.html`，文档中心卡片标题/摘要取自真实文档（原型已按此口径制作，数字与篇数随源仓库动态变化）；
  3. **GitHub 数据动态化**：构建时经 GitHub API 取 `fenixsoft/fenixd` 真实 stars/forks/open_issues，注入社区页数据卡（原型的 2.1k/318/47 为示例假数据）。
- 新增 GitHub Actions workflow `.github/workflows/deploy-pages.yml`：push 到 main 自动构建站点并发布 GitHub Pages（官方 actions 链：configure-pages → upload-pages-artifact → deploy-pages）。
- 新增一次性环境设置脚本 `scripts/setup_pages.sh`（gh 命令封装：确认远端仓库、启用 Pages（source=github-actions）、校验 workflow 权限）；其中 `gh auth login` 属一次性人工步骤，写入 README「人工步骤」小节与 `.fenix/todo.md`。
- 更新 `README.md`：补站点构建与部署说明。

## Capabilities

### New Capabilities
- `website-home-primary-pages`: fenixd 官网首页与一级页面（why/capabilities/docs/community）双语站点的构建、动态数据注入与 GitHub Pages 自动部署。

### Modified Capabilities
<!-- 无：本项目尚无已归档/活跃能力（spec/archive 与 spec/changes 均为空）。 -->

## Impact

- 新增：`specs/website-home-primary-pages/prototype/`（UI 真相源，本 SPEC 一并入库）、`build_site.py`、`scripts/setup_pages.sh`、`.github/workflows/deploy-pages.yml`
- 修改：`README.md`
- 产物目录 `site/dist/` 为构建产物，gitignore 覆盖、不提交（Pages 由 Actions 构建产出）
- 依赖：构建机可达 github.com（clone fenixd 源仓库 + GitHub API）；无 Python 三方依赖（标准库实现）
