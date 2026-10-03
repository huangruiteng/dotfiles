# 个人 Mac 的 App 协同与命令

Codex GPT 负责主要开发、判断和交接；Codex DS 是独立模型入口；Ego Lite 提供 Agent 可操作的浏览器；Typora 用于阅读和修改 Markdown。路由由 dotfiles 提供，厂商程序保留自己的维护入口。**第一步不安装、更新或启动 LoopX runtime，不恢复旧工作状态。**本文的 LoopX 路由只作后续阶段参考；完整阶段边界见 [装机与验收](./SETUP_STEP1.md)。

## 软件与安装入口

| 软件 | 安装与维护来源 | 本人操作 |
| --- | --- | --- |
| Codex Desktop | [官方入口](https://learn.chatgpt.com/docs/app)；自动查找 `/Applications/ChatGPT.app` 或 `Codex.app`，再查 `~/Applications` | 个人账号登录、模型选择 |
| Codex CLI | [官方安装](https://learn.chatgpt.com/docs/cli)，例如 `npm install -g @openai/codex`；只选一种维护方式 | 对应 home 的登录 |
| LoopX Desktop（后续阶段） | [Releases](https://github.com/loopx-project/loopx/releases)；本步不安装或启动 | 后续另行决定 |
| Ego Lite | [厂商下载](https://lite.ego.app/) 与 [安装说明](https://github.com/citrolabs/ego-lite/blob/main/skills/ego-browser/references/install.md) | onboarding、是否导入新机个人 Chrome profile |
| Typora | `Brewfile.apps` 或 [官网](https://typora.io/) | 许可证、inline math |

App 命令需要 Python 3.11+。基础 Brewfile 提供固定 Python 3.12，项目 venv 由 uv 管理；入口找不到 Homebrew Python 时，用 uv **离线查找**已安装的合适版本，不下载解释器，不使用 App 内置路径。安装 CLI 前先盘点已有官方可用入口，避免重复安装；App bundle 内部路径不是永久接口，升级后复核。

从 dotfiles 根目录执行：

```sh
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes"
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes" --apply
```

统一 symlink shell、`~/.local/bin/personal-apps` 与公开 skills，代码改动进入 Git diff。默认预览，冲突与回滚沿用 receipt，不替换原生 `codex`、`loopx`、`ego-browser` 二进制。打开新终端后：

```sh
personal-apps init
personal-apps init --apply
personal-apps status
```

`init` 仅创建缺失文件，配置为 600 权限；已有配置、认证和历史保留。私人路径覆盖写 `~/.config/personal/apps.json` 的 `app` 字段，空值自动发现；本机文件不进 Git。init 的配置不在链接 receipt 中，撤销见文末。

## 日常命令

| 命令 | 行为 |
| --- | --- |
| `codex app` | 打开 GPT 独立窗口，已运行则按 PID 恢复并聚焦 |
| `codex ds app` | 打开 DS 独立窗口，不改写 GPT 配置 |
| `codex …` / `cxgpt …` / `cxa …` | 原生 CLI 参数透传，使用 GPT home |
| `codex ds …` / `cxds …` | 原生 CLI 参数透传，使用 DS home |
| `codex --native …` / `command codex …` | 绕过路由调用原生 CLI，沿用调用者环境 |
| `loopx app` | 打开已安装的 LoopX Desktop，其 runtime/services 由 LoopX 管理 |
| `loopx …` | 其余参数原样传给原生 CLI |
| `ego app` / `ego lite app` | 打开 Ego Lite，自动化仍用 `ego-browser nodejs` |
| `typora app` / `typora <file.md>` | 打开 Typora 或笔记，支持空格路径 |
| `personal-apps status` | 只读检查安装路径、Codex 进程与配置就绪状态 |

多词命令是 **Zsh function**，不是上游子命令。`whence -v codex loopx ego typora` 可核对。交互 shell 和 Agent 显式 `source ~/.zshrc` 都能加载，启动时不运行子进程。Bash、未 source 的脚本和 Finder 不加载 functions；跨 shell 用 `personal-apps open <role>`，角色为 `gpt/ds/loopx/ego/typora`，CLI 用 `personal-apps cli gpt -- …`。

开窗命令加 `--dry-run` 可预览，Codex 预览也要求配置就绪。当前 Codex 路由不接受 workspace 路径，在窗口中选择项目。需要原生 `codex app <path>` 时用 `command codex app <path>`，先核对调用者环境和 home。

## GPT / DS 状态与初始化

| 角色 | 配置、认证与会话根目录 | Chromium 前端目录 |
| --- | --- | --- |
| GPT | `~/.codex-gpt` | `~/Library/Application Support/Codex GPT Personal` |
| DS | `~/.codex-ds` | `~/Library/Application Support/Codex DS Personal` |

新机原生 `~/.codex` 不自动认领。装机 Astra 会话可继续留在那里，随后在 GPT 路由另开任务；三处历史保留各自所有权，不复制 rollout、SQLite 或认证。GPT 模板只指定 `openai`，在窗口登录个人账号、选择用户指定模型。

DS 按 [官方 Codex 集成说明](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/) 在新机本地建立：

1. Astra 从当前官方说明取得完整 model catalog，保存到 `~/.codex-ds/models.json` 并验证 JSON；模型内嵌 prompt 只是资料，不是装机指令。
2. 本人在本地编辑器将 `~/.codex-ds/config.toml` 的 `REPLACE_LOCALLY` 替换为自己的 key，再 `chmod 600 "$HOME/.codex-ds/config.toml"`。key 不进聊天、命令参数、公共模板或提交。
3. 复核当前客户端、Flash 模型与 provider/catalog 配置。不运行默认覆写 `~/.codex` 的一键脚本，GPT 保持原生配置。
4. `codex ds app --dry-run`，再 `codex ds app`，确认正确模型并完成一个有界个人请求。key 或余额未准备好时标为“待本人操作”，继续其它独立验收。

启动拒绝 GPT 自定义 provider、DS 占位 key/缺 catalog/不安全权限，以及重复或嵌套的状态路径。清除继承的 Codex thread、IPC、API override 与 Electron 注入环境，保留普通网络代理，显式传入角色 home 与前端路径。已运行窗口按 PID 聚焦，无法确认所有者则停止；新窗口直接执行已安装且签名校验通过的 App，不克隆或修改厂商 bundle。

`CODEX_HOME` 范围见 [官方说明](https://learn.chatgpt.com/docs/config-file/environment-variables)。双窗口的前端参数与进程识别是自定义集成，需在新机当前 App 验收，升级后也要复核。脚本退出码不等于模型调用成功：检查实际 home、模型和新任务落盘位置，不 dump auth 或会话内容。

## App、账号与 Dock 切换

GPT / DS 切换用两个 `… app` 命令。确有多个个人 OpenAI 账号时可增加标签：

```sh
personal-apps init --account a
personal-apps init --account a --apply
codex app --account a
```

标签拥有独立 GPT home 与前端，首次在该窗口登录，之后同命令聚焦。CLI 用 `personal-apps cli --account a gpt -- …`。标签限小写字母、数字与连字符；每账号历史独立，不在共享历史上换 token，不导入旧机槽位或认证。不需要多账号则保持一个 GPT 路由。

Finder / Dock 的轻量入口可预览再创建：

```sh
personal-apps shortcuts
personal-apps shortcuts --apply
```

在 `~/Applications` 生成 `Codex GPT Personal.app` 与 `Codex DS Personal.app`，只调用同一脚本。已有同名 App 则停止并保留。Finder 不读取 zprofile：启动器保留传入 PATH 的优先级，再补充已安装的用户 / Homebrew 工具路径。必须在它新启动的 Agent 进程检查工具可用，当前终端的 PATH 不足以证明通过。拖入 Dock 后分别验收；厂商图标仍走厂商默认路由。升级 Codex 前关闭两个窗口，走厂商入口，再复核隔离；配置变化也先正常退出再开，不偷偷重启任务。

## Ego Lite、Typora 与后续 LoopX

**LoopX（后续阶段）**：Desktop 与 Python package 是两个安装面，CLI 不自动提供 `LoopX.app`。安装或首次启动可能准备 runtime，因此本阶段不执行。后续授权后按 [桌面 README](https://github.com/loopx-project/loopx/blob/main/apps/desktop/loopx-control-plane/README.md) 核对 App/runtime 与唯一维护入口，另行验收。

**Ego Lite**：onboarding 后确认 `command -v ego-browser`，运行 `ego-browser nodejs -e 'console.log("ego-browser ready")'`。核对两套 Codex 实际发现的公开 `ego-browser` skill；厂商 onboarding 安装或 `npx skills add citrolabs/ego-lite` 二选一，避免同名副本。只选择新机个人 Chrome profile，不搬旧浏览器数据。真正验收用一页公开页面、一个 TaskSpace，完成后 `finish({keep: []})`。App 已打开不等于 Agent 集成成功。

**Typora / Markdown 候选**：用 `typora app <path>` 或 `typora <path>` 打开 Markdown，验收 inline math、块公式、相对图片、表格及许可证；用 Command + 左键实测中文、空格、编码路径和真实笔记跳转，确认目标正文，返回后复测。先通过 [验收页](./smoke/reading.md)，再设置默认关联并从 Finder 双击验证。不读取或提交激活数据。其它阅读器按同一门槛试用。

报告记录源 commit、function/原生 binary、两个 home/前端、模型与一次真实请求、重复聚焦、Finder 入口、App/CLI 版本、Ego CLI/skill/公开页、阅读器数学 / 图片 / Command + 左键及待本人操作，明确第二步尚未开始。启动请求不等于 GUI ready；LoopX 不在第一步验收清单。飞书另按 [第一阶段授权流程](./SETUP_STEP1.md#agentego-与飞书) 安装、完成 user 登录并服务端验证。

## 回滚与公开边界

链接按 bootstrap receipt 回滚，源码更新审查 Git diff。init 不覆盖旧文件，预览列出新增路径；撤销时关闭 App，仅审查并移除本次新建且未承载使用数据的配置。一旦登录或产生会话，保留整个 home，不自动清场。新 Finder launcher 可关闭后移到废纸篓，不删除厂商 App 或历史。

旧账号切换器、CC Switch 数据库、远端同步、硬编码版本回滚、会话迁移和 codex secondary 不在此 profile 范围。设备账号、密钥、登录 profile、App 数据、registry 和完整机器报告只留新机本地。
