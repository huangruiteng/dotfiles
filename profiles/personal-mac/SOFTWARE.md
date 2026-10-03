# 个人 Mac 软件与偏好

这份清单综合日常使用的软件类别与根 README 的安装笔记，作为新机选择和验收的依据。它不是整台旧机器的清单，也不包含账号、主机、许可证或应用数据。入口于 2026-10-02 核验；安装时再检查官方支持的 macOS 与 Apple Silicon 版本。

## 起步安装

| 软件 | 用途与保留偏好 | 官方入口 / Homebrew cask |
| --- | --- | --- |
| iTerm2 | 默认 Meslo Nerd Font / 黑底 Pastel，完整分段 Git prompt；实际检查旧会话与新窗口的箭头 | [官方](https://iterm2.com/) / `iterm2` + `font-meslo-lg-nerd-font` |
| Typora | 中文 Markdown、公式、相对路径配图；开启 inline math，试读含块公式的笔记 | [官方](https://typora.io/) / `typora`；激活由本人完成 |
| Google Chrome | 日常浏览和需要 Chrome 的网页工具；新建个人 profile | [官方](https://www.google.com/chrome/) / `google-chrome` |
| The Unarchiver | 解压归档、处理文件名编码 | [官方](https://theunarchiver.com/) / `the-unarchiver` |
| KeepingYouAwake | 长任务期间按需防休眠；使用有期限的会话 | [官方](https://keepingyouawake.app/) / `keepingyouawake` |
| 一个主编辑器 | VS Code 或已有偏好的 Cursor / Trae，任选一个；Sublime Text 可另作轻量文本查看器 | [VS Code](https://code.visualstudio.com/)、[Cursor](https://cursor.com/)、[Trae](https://www.trae.ai/)、[Sublime Text](https://www.sublimetext.com/) |
| 桌面 Agent 客户端 | 官方发行、个人账号；模型选项以当前账号为准 | [OpenAI 官方入口](https://learn.chatgpt.com/docs/app) |
| Ego Lite | Agent 浏览器；onboarding 后验收 CLI 和公开 skill | [官网](https://lite.ego.app/) / [公开技能仓库](https://github.com/citrolabs/ego-lite) |

前五项与 Meslo 字体用 `Brewfile.apps` 安装，CLI 基线独立。先盘点已有应用再补缺项；Codex GPT/DS 启动和命令验收按 [APP_WORKFLOW.md](./APP_WORKFLOW.md) 执行，不克隆旧机副本或回滚版本。登录、许可证与系统权限由本人处理；防休眠不自动开启所有登录项。第一步不安装、更新或启动 LoopX runtime。

## 按需补充

| 场景 | 软件 | 选择条件与边界 |
| --- | --- | --- |
| 后续长程工作 | [LoopX Desktop](https://github.com/loopx-project/loopx/releases) | 后续阶段单独授权、安装与验收；本阶段不启动，不接续状态 |
| 飞书 CLI | [lark-cli](https://github.com/larksuite/cli) | 用户需要连接飞书时安装官方发行；校验 checksum，本机配置后完成 user 授权与服务端验证，不输出身份与凭证 |
| Markdown 候选 | ColaMD 或其它阅读器 | 先试用 [阅读验收页](./smoke/reading.md) 和真实笔记，Command + 左键通过后再决定默认关联；记录不支持的渲染项 |
| 文献阅读 | [Mendeley Reference Manager](https://www.mendeley.com/download-reference-manager/macOS/)（`mendeley-reference-manager`） | 需要文献库再装；重新登录个人账号，只导入本人有权持有的论文与批注 |
| 模型额度观察 | [CodexBar](https://codexbar.app/)（`codexbar`） | 需要菜单栏用量视图再装；逐 provider 在新机授权，不复制登录数据库 |
| 多 provider 配置 | [CC Switch](https://github.com/farion1231/cc-switch)（`cc-switch`） | 确实使用多服务商时再装；它能管理敏感配置，密钥只在新机本地输入 |
| PDF / OCR / 媒体 | poppler、tesseract、ffmpeg | 从 `Brewfile.optional` 按任务选取；不安装就不承诺对应处理能力 |
| 容器 | Colima + Docker CLI / Compose | 有实际测试依赖时安装；VM 的内存、磁盘与开机启动另行决定 |
| C++ / 模型源码 | CLion 或编辑器 + clangd / CMake / LLDB；CMake、Ninja、pkgconf | 先选一条工具链，避免重复索引器；NVIDIA 专用调试器留给确有远端 GPU 任务时评估 |
| 办公与协作 | Microsoft Office、个人 OneDrive、腾讯会议、Discord、微信 | 从厂商官网或 Mac App Store 选择；使用个人账号与许可证，不导入组织托管 profile |
| 日常体验 | 网易云音乐、豆包客户端 / 输入法、个人邮件客户端 | 保留为偏好选项；本人决定账号、默认输入法、同步范围与通知 |

## README 中的偏好如何延续

- **触控板轻点**：在系统设置中按本人习惯启用，验证手势即可，不批量覆盖系统偏好。
- **终端外观与回看**：默认交付 Meslo / Pastel 与有界 10000 行回看；安装器预览并备份冲突，允许显式退出默认外观。不要导入包含命令、环境或服务器地址的旧 profile。
- **Shell**：默认恢复完整 Git alias / helper、fzf、zoxide 的 autojump 兼容入口、补全、autosuggestions、syntax highlighting、history substring search 和 Git dirty prompt。旧 zplug 的启动下载 / 更新职责不恢复；公共能力随固定来源交付。缺依赖时启动仍可用，但 doctor 报告缺项，不能当作完成。
- **编辑器**：先装语言所需的扩展，如 Python、EditorConfig、GitLens、CMake / clangd；Remote SSH 仅在有个人远端时配置，服务器列表不进公共 profile。
- **浏览器**：密码管理器、内容拦截、截图、样式扩展按需选择；先核查官方商店维护状态与权限。旧 README 的扩展名不等于今天仍适用，不批量恢复插件或浏览器数据。
- **暂缓项**：Hammerspoon / Karabiner 在原 README 中已搁置；QuickJump、MailMaster 与 EasyStart 等历史或同名工具，先确认准确项目、维护状态及实际用途，不能凭名字自动下载。旧 Linux apt / 调试工具清单不照搬到 macOS。
- **组织管理工具**：VPN、终端管理、安全代理、内部插件及工作账号由组织按其流程管理，不作为个人 Mac 的依赖。

## Astra 必须完成的软件整理

1. 读取本表、profile README、根 README 的软件与偏好段落；根 README 只作历史参考，不执行其中旧 bootstrap、身份或 SSH 示例。
2. 只枚举新机应用名称与工具版本，和本表对照，产出“已有 / 安装 / 暂缓 / 需本人操作”四种结果；详细机器清单只留本机。
3. 安装缺项；同类选择已有偏好，来源不明的条目记为暂缓。GUI 应用验收和命令行验收分别报告。
4. 本机 `SETUP_REPORT_STEP1.md` 至少记下：软件、用途、官方来源、实际版本、决定、启动验证、设置验证、真实请求、需要本人完成的登录或许可证事项。报告同时核对阅读器数学/图片/Command + 左键相对链接、终端新 shell 与 Git alias、完整 checkout、技能发现、编辑器项目打开、解压与定时防休眠，明确第二步尚未开始。

偏好和安装检查是交接的必要步骤；仅完成 `brew bundle` 或复制这份清单不能算完成。
