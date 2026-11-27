## 2026-11-26

- 自上次自省以来无 SPEC 活动，跳过自省。

## 2026-11-27

- 自上次自省以来无 SPEC 活动，跳过自省。

## 人工步骤（SPEC website-home-primary-pages · GitHub Pages 上线）

- [x] `gh auth login`：GitHub CLI 认证（2026-11-27 admin 处置时点核验：已认证账号 fenixsoft，含 repo+workflow scopes）。
- [x] GitHub Pages 启用与首次部署（2026-11-27 admin 处置核验）：Pages 已启用且 build_type=workflow，push main 触发 deploy-pages workflow success，五页实测全 200，站点已上线。
- [ ] `scripts/setup_pages.sh` 缺陷待修（产品脚本，走评审链，不由 admin 热修）：步骤 3/4 校正分支的 build_type 字面量 `github-actions` 非法——GitHub API 仅接受 `legacy`/`workflow`（HTTP 422 实证），对已启用（build_type=workflow）的仓库重跑会在校正分支 exit 1；应改为以 `workflow` 为正确值做幂等判定。
- 完成判定：~~推送 main 触发 deploy-pages workflow 跑绿，https://fenixsoft.github.io/fenixd-website/ 五页全 200~~ ✅ 已达成（2026-11-27 实测）。

## 2026-11-28

### 浪费
- **bigmodel API 停滞 50 分钟贯穿 10 run**
  - 自进化：问题成立 / 建议部分合理 / — 不需要
  - 影响：近 24 小时窗内 14 个 run 有 10 个在 bigmodel.cn@glm-5.3-flash 腿上发生 API 停滞（单次请求往返长时间无响应的空转等待），合计停滞 3007.2 秒≈50.1 分钟纯墙钟等待；最严重单 run 是验证裁决第 1 轮（1045.9 秒 API 时长中停滞 739.0 秒，占 70.7%）。无 run 失败，但全链交付墙钟被显著拉长。
  - 证据：逐 run 回源各 transcript 的 run_metrics（框架逐 run 延迟汇总记录）：planner-judge-website-home-primary-pages-1795752817-a1 stalls=3 total=739.0s max=514.3s；planner-judge-...-1795754185-a1 stalls=1 total=534.2s；planner-plan-...-1795751556-a1（计划起草，即当日初筛离群 run：136 turns/72 文本轮/19.6 分钟/$5.04）stalls=5 total=567.5s，停滞占其墙钟 48.2%；code-review-1795798963 的 bigmodel 腿 1 次 187.3 秒停滞后遇 429，同 run 换道 deepseek 腿 41 turns 零停滞——同窗同机对照。
  - 调查评估：暴露于 website-home-primary-pages SPEC 全链（plan/impl/judge/admin 车道均中招）。已核实：停滞数字全部回源当晚 transcript 内 run_metrics 原始记录，非转引摘要；汇总口径为 10 个停滞 run 的 stall 合计（整窗量，非单车道分量）。根因未定、两假说并存：主假说 bigmodel 服务端限流/降级（硬 429 触发换道 + deepseek 对照腿零停滞佐证），本地网络假说无证据支持但不排除——故只下形态层结论：本窗 bigmodel 腿普遍慢、deepseek 腿干净。与存量工作关系：429 硬错误已有 escalation chain（车道候选换道环）承接，停滞形态无对应机制（见 improvements 配套条目）。结论：约 50 分钟为可止损的纯等待，run 全部成功收尾故无产出损失，属过程性浪费。
  - 建议：短期先把停滞观测升级为信号：日汇总将「单 run 停滞合计>600s 或单次>300s」记 info 级信号留痕（当前只进离群深扫，无实时信号）；机制性止损由 improvements 条目「停滞阈值换道」承接。

### 失误
- **code-fix 车道误伤无测试项目，回归信号三度重发**
  - 自进化：问题成立 / 建议部分合理 / — 不需要
  - 影响：周期 code-review（自动代码评审）01:02 产出 17 条 findings（含 2 条 major 正确性缺陷：build_site.py:238 与 build_proto.py 的 _md_inline 内联代码未做 HTML 转义，`<name>` 类占位符在产物文档中被吞）后，code-fix 车道（评审发现的自动修复车道）因 verify.yaml 缺 regression 段 fail-closed（缺件即拒派）拒派批次，17 条 findings 至窗末 0/17 修复（.fenix/code-review/fix-progress.json：phase=blocked，reason=regression_section_missing）；信号三度重发（本地 01:08:50、01:37:37、02:07:37，第三发在窗闭后 5 分钟实测仍在发生），已烧 2 个 administrator（管理员处置）run 重复同一结论，合计 $2.80、约 710 秒 API 时长、63 turns。
  - 证据：告警 3a1ac2fbcce4（首轮 verify_regression_missing 信号，01:08:50）→ admin-fenixd-website-1795799564（$0.82/19 turns）resolved；告警 87d44d0d0df5（重发，01:37:37，距上轮 resolved 23 分钟）→ admin-fenixd-website-1795801064（$1.98/44 turns）升级人工二选一；信号 521266aaa6fe（第三发，02:07:37）。源码级根因：.fenix/core/code_fix.py:3958 _signal_inflight（信号在途去重门）跳过 handled/escalated 记录——处置一完成即失去去重保护；code_fix.py:5910 守卫对 regression is None 一律 fail-closed、无「无测试体系」豁免口。
  - 调查评估：暴露于 fenixd-website 项目级 code-fix 车道（对已 done 的 website-home-primary-pages 做售后维护批时触发）。已核实事实：admin_alerts.json 30 条记录时间线、两 run transcript 终态字段、守卫与去重门源码行、fenixd.log 18:02:45Z 周期回归巡逻对同一情形仅 INFO 级跳过。根因：框架层缺口（无测试体系豁免缺失 + 去重门对已升级信号失效），非 administrator 处置失误——两轮处置均按手册得出同一正确结论（项目确无测试体系，regression 段依 .fenix/verify.yaml 2026-11-27 头注有意省略），第二轮已正确识别结构死环并升级人工。与存量工作关系：spec/changes/ 仅 website-home-primary-pages（已 done）、spec/archive/ 为空，无在飞 SPEC 与此相关，非重复立项。结论：结构性死环，升级 7eb7f1e8c368 的人工裁决是当前唯一出口，重发环每约 30 分钟将继续消耗 administrator run。
  - 建议：人工对升级 7eb7f1e8c368 尽快二选一，建议优先「声明无测试体系」方向而非整体停用 code-fix 车道（保住后续 findings 自动修复能力；两选项原文在处置记录 48e8f3a15ef4）；17 条 findings（2 条 major 转义缺陷）在车道解除前需人工修复或另立 SPEC。框架侧豁免通道见 improvements 配套条目。

### 可改进
- **API 停滞无换道机制，单次空转最长 534 秒**
  - 自进化：问题成立 / 建议合理 / ✓ 值得立项 · 处理：待处理 · 删除：否
  - 影响：复发敞口：bigmodel 腿停滞形态复现时，同等规模（14 run）的一日将再损失约 50 分钟墙钟（本窗实测 3007.2 秒），且单次空转可长达 534.2 秒（≈8.9 分钟）无任何换道或止损动作。
  - 证据：对照实验已在本窗自然发生：code-review-1795798963 在 bigmodel 腿 187.3 秒停滞后遇 429（限流硬错误），escalation chain（车道候选换道环）立即切换 deepseek@deepseek-flash（fenixd.log 2026-11-27T17:06:16Z [provider switched] 记录，chain_index=1，attempt 2/2），后腿 41 turns 零停滞完成——429 有换道、长停滞没有，机制不对称；停滞样本见 waste 条目 run_metrics 回源数字。
  - 调查评估：暴露于 website-home-primary-pages 全链。已核实：run_metrics 双腿对照与 provider_marker（换道标记）记录均在 transcript 内。根因归属：机制缺口——停滞（无错误返回的慢流）不在换道触发条件内，与 429 共用同一换道路径却缺触发；停滞本身的根因未定（服务端降级 vs 本地网络，见 waste 条目），但本提案不依赖根因裁决——无论停滞源于何端，换道均对称有效。与存量关系：escalation chain 换道机制已存在，本条是同路径新增触发条件，非新建机制，非重复立项。结论：证据充分、可立项，新 agent 可据此直接起草 SPEC。
  - 建议：SPEC 提案：runner 层增加停滞换道——单次 API 往返空转超过阈值（建议 300 秒，本窗实测两个 8 分钟级空转样本 514.3s/534.2s）即向 escalation chain 后候选换道（与 429 同路径、共享 attempt 计数），同时把停滞明细（次数/时长/触发换道与否）落盘供回溯；需带防抖（候选环单轮最多换道一次，避免慢而活的候选被频繁跳过）。

- **回执落地核验误报升级，重验 83 秒直达 done 不被认账**
  - 自进化：问题成立 / 建议部分合理 / — 不需要
  - 影响：已发生 1 条 major 误报升级挂起：env_fix_receipt_unverified 4d9d041fd54c（处置回执落地校验失败告警）——实际重验已 22/22 全绿交付 done，处置回执却被错标 receipt_landing=invalid（对账语义失真）；复发敞口：每次「复位重验走快道直达 done」都会复发，单次清理代价 1 个 administrator run（本窗同车道实测 $0.49-$2.21/个）。
  - 证据：时间线已核实：13:05:01 administrator 收 verify_env_blocked（验证环境阻塞信号：pages-live-deployed 场景因 Pages 未上线五页 404 而阻塞）；13:07:02 处置（run admin-website-home-primary-pages-1795755901）写 resolved 并复位重验；13:08:25 重验 22/22 全绿、STATE（框架规格状态账）直达 done（verification-report.md 合成时间戳与 STATE.md updated 一致）；13:17:41 判定窗（10 分钟）满，核验判 invalid 并发升级。源码根因：core/admin_monitor.py:1520 env_fix_receipt_landed 双通道——① STATE 状态严格等值 expected_status（testing），快道 83 秒内 testing→done 直落，窗满采样只见 done；② 仅认 .fenix/runs/ 下 verify- 前缀 run 文件，而本轮重验为 in-process（框架内部验证，不落外部 run 文件：runs 归档 14 个文件无一 verify-*，却完成了一轮 22 场景全量验证），通道②同样落空。
  - 调查评估：暴露于 website-home-primary-pages（已 done）的 env 阻塞处置链。已核实事实：处置记录 74f4260cd981（resolved）、验证报告头 22/22、STATE.md 终态 done、双通道源码语义逐行读核。根因：落地判定过窄——「done」严格强于预期终态 testing+verified，却不算有效落地；in-process 重验产物也不被通道②识别。与存量工作关系：spec/changes/ 无在飞相关 SPEC、archive 为空，非重复立项。结论：结构性误报，且升级告警缺「宿主 spec 已终态自动失效」机制，将永久挂起误导后续人工。归因到单因确定性（源码级），非多假说形态。
  - 建议：SPEC 提案：env_fix_receipt_landed 增加「entry.status==done 视为有效落地（强于预期终态）」分支，并把 in-process 重验的产物指纹（verification-report 轮次指纹）纳入通道②证据；同批给升级告警加宿主终态自动失效（spec done 时未决升级自动闭环留痕）；先人工关闭挂起的 4d9d041fd54c。

- **回归契约三处口径不一，缺无测试体系豁免通道**
  - 自进化：问题成立 / 建议合理 / ✓ 值得立项 · 处理：待处理 · 删除：否
  - 影响：复发敞口：不做豁免通道，code-fix 车道对无测试体系项目持续 fail-closed，每约 30 分钟重发一次信号、每发消耗 1 个 administrator run（本窗实测单 run $0.82-$1.98）；本仓 17 条 code-review findings 修复链持续受阻。
  - 证据：同一情形（verify.yaml 有意省略 regression 段，头注 2026-11-27 已记载「项目无测试体系，不臆造命令」理由）在框架三处组件三种口径：code_fix.py:5910 fail-closed 拒派并发信号；dashboard regression_routes.py:353 autodraft 官方口径「项目无可用测试体系时维持原契约不变并输出 no_test_system marker 结案」；周期回归巡逻 admin_monitor.py:5126 仅 INFO 级「缺段跳过周期回归」（fenixd.log 18:02:45Z 实测该日志）。
  - 调查评估：暴露于 fenixd-website 项目级 code-fix 车道。已核实：三处源码/日志行逐处读核，契约头注在位。根因：框架组件间政策不一致，缺共享的「无测试体系」声明位（如 verify.yaml 契约内 skipped 标记），使各组件各自推断且互不认账。与存量工作关系：administrator 第二轮处置（记录 48e8f3a15ef4）已给出人工二选一（两选项均含停用 code-fix 车道），本条与之互补而非重复——契约内豁免通道保住车道不整体停用，可并行呈报人工。结论：框架侧提案（本车道铁律不改框架代码），落地后 mistakes 条目所述重发环与车道误伤同步消解。
  - 建议：向 Fenix 框架仓库提案：code-fix 车道守卫识别 verify.yaml 契约内「无测试体系」声明标记（省略段+声明=跳过回归门并静默、不再发信号），三处组件（code_fix 守卫/dashboard autodraft/周期巡逻）共用同一判定函数；本仓短期以人工裁决升级 7eb7f1e8c368 兜底。
