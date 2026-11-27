# fenixd-website

Fenix 框架（fenixd，Fenix Loop Engineering Framework）的官方网站项目，用于呈现框架的产品介绍、能力说明、文档入口与社区信息。

本工程由 Fenix 框架自身管理：通过 `.fenix/` 骨架接入 fenixd daemon，以 SPEC 闭环驱动网站的设计、实现与验证。

## 站点

- 界面真相源：`specs/website-home-primary-pages/prototype/`（五页 HTML：index / why / capabilities / docs / community；品红极光配色、中英双语、熵增叙事；设计约束见根目录 [`DESIGN.md`](DESIGN.md)）。
- 技术形态：零外部依赖的纯静态 HTML/CSS/JS，无框架、无运行时构建；构建脚本为 Python 标准库实现。
- 动态数据（构建时注入，站点本体无后端）：
  - `help/*.html` 渲染页与 docs.html 文档卡片：浅克隆 [fenixsoft/fenixd](https://github.com/fenixsoft/fenixd) 的 `docs/help/*.md`，以原型自带渲染管线生成；
  - community.html 数据卡 stars / forks / open issues：GitHub 公共 API 真实值（API 失败时注入 `--` 占位并打印 WARN，构建不失败）。
- 构建时同步净化原型脚手架（仿样横幅、annotator.js、配色 dock），站点交互（中英切换、移动端菜单、灯箱）与原型一致。

## 本地构建与预览

```bash
python3 build_site.py                                 # 构建到 site/dist/（净化 + 文档渲染 + 数据注入 + 完整性校验 + 本地冒烟）
python3 -m http.server 8000 --directory site/dist     # 人工预览 http://localhost:8000
```

要求：Python 3.10+（仅标准库）、git、网络可达 github.com（clone 源仓库与 GitHub API）。源仓库缓存于 `.site-cache/`（已 gitignore），删除后自动全量重建；`site/dist/` 为构建产物（已 gitignore），每次构建原子替换。

## 部署（GitHub Pages）

push 到 main 自动触发 [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)：构建站点后经官方 Actions 链（actions/configure-pages → actions/upload-pages-artifact → actions/deploy-pages）发布到 `https://fenixsoft.github.io/fenixd-website/`。并发组自动取消同分支旧部署。

## 人工步骤（一次性）

1. `gh auth login`：完成 GitHub CLI 认证（交互式，无法由 Agent 代做）。
2. `bash scripts/setup_pages.sh`：启用 Pages（build_type=github-actions）并校验 workflow 权限；幂等可重跑，未认证时给出指引退出。
3. 完成判定：推送 main 后 deploy-pages workflow 跑绿，`https://fenixsoft.github.io/fenixd-website/` 五页全 200。
