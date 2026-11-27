## 2026-11-26

- 自上次自省以来无 SPEC 活动，跳过自省。

## 2026-11-27

- 自上次自省以来无 SPEC 活动，跳过自省。

## 人工步骤（SPEC website-home-primary-pages · GitHub Pages 上线）

- [ ] `gh auth login`：GitHub CLI 认证（一次性人工步骤，交互式，Agent 不代做认证）。
- [ ] `bash scripts/setup_pages.sh`：启用 GitHub Pages（build_type=github-actions）并校验 workflow 权限（幂等，可重复执行）。
- 完成判定：推送 main 触发 deploy-pages workflow 跑绿，https://fenixsoft.github.io/fenixd-website/ 五页（index / why / capabilities / docs / community）全 200。
