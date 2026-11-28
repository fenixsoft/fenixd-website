# fenixd 安装指引（供 AI harness 读取执行）

本页是 Fenixd 官网提供的机器可读安装入口。若你（AI agent / harness）被用户要求安装 fenixd，请按以下步骤执行。

## 给 harness 的执行指令

1. **完整读取官方部署手册**：

   <https://raw.githubusercontent.com/fenixsoft/fenixd/refs/heads/main/docs/install.md>

2. **按手册 §0 判断用户环境**：Claude Code CLI 通道（缺省）与 dsh web 通道二选一或双装，据此确定要走的安装路径。
3. **严格按手册对应章节执行**：通用前置（§1）→ 安装 fenixd 框架（必装，Release 制品或 git clone）→ 按需装配 dsh 插件全家桶（dsh 环境走 dsh 装配手册）。
4. **完成验收**：按手册验收章节逐项验证（CLI / daemon / dashboard），向用户报告结果与遗留项。

## 注意事项

- **不要凭记忆安装**：手册含版本兼容表与安装器硬门（如 claude CLI 为安装器硬门），一切以手册当前内容为准。
- **凭据缺失时明确告知用户补齐**（GitHub token、LLM key 等），不要猜测或跳过。
- Windows 与 Linux 的 daemon 服务承载不同（NSSM / systemd user unit），按手册平台章节执行。
- 安装作用于用户**现有的** harness 环境（dsh 桌面版 / dsh web / Claude Code 全局 skills），全程不新建并行环境。

## 相关资源

- 仓库：<https://github.com/fenixsoft/fenixd>
- dsh 插件装配手册：<https://raw.githubusercontent.com/fenixsoft/dsh-plugins/refs/heads/main/docs/install-dsh-plugins.md>
- 官网：<https://dev.icyfenix.cn/>
