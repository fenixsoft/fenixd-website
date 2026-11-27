## 2026-11-26

- 自上次自省以来无 SPEC 活动，跳过自省。

## 2026-11-27

- 自上次自省以来无 SPEC 活动，跳过自省。

## 人工步骤（SPEC website-home-primary-pages · GitHub Pages 上线）

- [x] `gh auth login`：GitHub CLI 认证（2026-11-27 admin 处置时点核验：已认证账号 fenixsoft，含 repo+workflow scopes）。
- [x] GitHub Pages 启用与首次部署（2026-11-27 admin 处置核验）：Pages 已启用且 build_type=workflow，push main 触发 deploy-pages workflow success，五页实测全 200，站点已上线。
- [ ] `scripts/setup_pages.sh` 缺陷待修（产品脚本，走评审链，不由 admin 热修）：步骤 3/4 校正分支的 build_type 字面量 `github-actions` 非法——GitHub API 仅接受 `legacy`/`workflow`（HTTP 422 实证），对已启用（build_type=workflow）的仓库重跑会在校正分支 exit 1；应改为以 `workflow` 为正确值做幂等判定。
- 完成判定：~~推送 main 触发 deploy-pages workflow 跑绿，https://fenixsoft.github.io/fenixd-website/ 五页全 200~~ ✅ 已达成（2026-11-27 实测）。
