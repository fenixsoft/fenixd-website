#!/usr/bin/env bash
# setup_pages.sh · GitHub Pages 一次性环境设置（gh 命令封装，幂等可重跑）
#
# 步骤：校验 gh 已认证 → 确认远端仓库 → 启用/校正 Pages（build_type=github-actions）
#       → 校验 workflow 默认权限 → 输出 Pages 状态与首次部署触发提示。
# 认证（gh auth login）是一次性人工步骤，交互式，脚本不代做：未认证时输出明确指引并退出 1。
set -euo pipefail

REPO="fenixsoft/fenixd-website"
PAGES_URL="https://fenixsoft.github.io/fenixd-website/"

echo "[setup] 1/4 校验 gh 认证状态"
if ! gh auth status >/dev/null 2>&1; then
  echo "错误：gh 未认证。请先运行 gh auth login（一次性人工步骤），完成后重跑本脚本。" >&2
  exit 1
fi
echo "  已认证 ✓"

echo "[setup] 2/4 确认远端仓库 ${REPO}"
if ! gh repo view "${REPO}" >/dev/null 2>&1; then
  echo "错误：无法访问仓库 ${REPO}（不存在或无权限）。" >&2
  exit 1
fi
echo "  仓库可访问 ✓"

echo "[setup] 3/4 启用/校验 GitHub Pages（build_type=github-actions）"
pages_json="$(gh api "repos/${REPO}/pages" 2>/dev/null || true)"
if [ -z "${pages_json}" ]; then
  echo "  Pages 未启用，正在启用（build_type=github-actions）…"
  gh api -X POST "repos/${REPO}/pages" -f build_type=github-actions >/dev/null
  echo "  已启用 ✓"
else
  build_type="$(printf '%s' "${pages_json}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("build_type",""))')"
  if [ "${build_type}" = "github-actions" ]; then
    echo "  Pages 已启用且 build_type=github-actions ✓（幂等，无需变更）"
  else
    echo "  Pages 已启用但 build_type=${build_type}，校正为 github-actions …"
    gh api -X PUT "repos/${REPO}/pages" -f build_type=github-actions >/dev/null
    echo "  已校正 ✓"
  fi
fi

echo "[setup] 4/4 校验 workflow 默认权限"
wf_perm="$(gh api "repos/${REPO}/actions/permissions/workflow" 2>/dev/null \
  | python3 -c 'import json,sys; print(json.load(sys.stdin).get("default_workflow_repository_permissions",""))' || true)"
if [ -n "${wf_perm}" ] && [ "${wf_perm}" != "write" ]; then
  echo "  警告：default_workflow_repository_permissions=${wf_perm}（非 write）。" >&2
  echo "  如部署失败，请在仓库 Settings → Actions → General 提升为 Read and write。" >&2
else
  echo "  workflow 权限 OK ✓"
fi

echo "[setup] Pages 当前状态："
gh api "repos/${REPO}/pages" --jq '{status: .status, build_type: .build_type, html_url: .html_url}' 2>/dev/null || true
echo "[setup] 首次部署触发：向 main 分支推送（merge）即自动构建发布（.github/workflows/deploy-pages.yml）。"
echo "[setup] 完成判定：${PAGES_URL} 五页（index/why/capabilities/docs/community）全 200。"
