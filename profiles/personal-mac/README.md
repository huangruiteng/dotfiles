# Personal Mac profile

面向 Apple Silicon 的个人开发配置，适合从公开资料重建日常工具和 shell 能力。先读 [第一阶段完整流程](./SETUP_STEP1.md)：完整 checkout、默认 Git 插件与终端外观、Markdown Command + 左键跳转、真实请求及撤销入口均需验收。不读取旧 SSH、账号或设备配置。

## 安装与验收

先在新机完成 [Xcode Command Line Tools 与 Homebrew](https://docs.brew.sh/Installation)，再从本仓库根目录执行：

```sh
brew bundle install --file profiles/personal-mac/Brewfile --no-upgrade
```

随后取得审查提交的完整 dotfiles / CS-Notes checkout，放到稳定目录；bootstrap 会拒绝缺文件或 sparse checkout。将 shell 与审查后的 skills 一起链接到用户目录：

```sh
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes"
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes" --apply
```

默认是预览；`--apply` 才写入。旧配置冲突先阅读，确定替换后加 `--replace`，安装器将原文件或 symlink 移入备份并返回回滚 receipt。不会覆盖 SSH、Git 身份、编辑器配置或 App 数据。shell 安装同时链接 `~/.local/bin/personal-apps`、tmux 和 macOS iTerm Dynamic Profile；`--no-preferences` 跳过 tmux/iTerm。只装 shell/命令用 `--shell-only`，只装技能用 `--skills-only`。skills 默认位置是 `~/.agents/skills`，通过 symlink 修改直接进入 CS-Notes 的 Git diff。`--allow-export` 仅用于额外审查过的非 Git 导出，不能证明 checkout 完整。

`node@24` 的 bin 目录在没有现有 Node 时作为后备 PATH；已激活的环境优先。若当前 Node 不是 24，按实际项目选择，不覆盖版本管理器。私人配置放到 `~/.config/personal/zshrc.local`，示例见 `zshrc.example`。详见 [shell 与链接维护](../../docs/SHELL.md)。不运行 `brew bundle cleanup`。

Python 的固定 App 运行时由 Brewfile 的 `python@3.12` 提供，项目使用 uv 和独立虚拟环境。Node 默认一套 24 LTS，仓库另有要求时按锁文件/版本约束安装；不要把 App 自带的 Node、Python、pnpm 路径当成系统依赖。Rust、Go、pnpm、容器和 OCR 等按实际项目安装。

`gitconfig.example` 不含身份信息；本人在新机设置 Git 名称和邮箱，GitHub 认证在新机进行。凭证、SSH 私钥和账号配置不放进这个 profile。

```sh
bash profiles/personal-mac/verify.sh
brew bundle check --file profiles/personal-mac/Brewfile
```

检查脚本只读，不登录、不联网、不启动服务。`Brewfile.optional` 是按需索引；若只需 PDF 提取，安装 `poppler` 即可，不必整份安装。

## 图形软件与长期维护

先读 [软件与偏好清单](./SOFTWARE.md)，核对已有软件、根 README 的历史偏好和新机用途。选定的 GUI 起步清单独立放在 `Brewfile.apps`，包括 iTerm2、Typora、Chrome、The Unarchiver、KeepingYouAwake 与 Meslo Nerd Font：

```sh
brew bundle install --file profiles/personal-mac/Brewfile.apps --no-upgrade
```

桌面 Agent 客户端与一个主编辑器从官方入口安装，登录与许可证由本人处理。[App 协同与命令](./APP_WORKFLOW.md) 包含 `codex app`、`codex ds app`、Ego Lite、Typora、状态隔离与 Finder/Dock 入口，需单独初始化和验收。LoopX 路由只作后续阶段参考，本步不安装、更新或启动其 runtime。Mendeley、CodexBar、CC Switch、办公 / 日常应用按清单决定，报告记录安装、暂缓及设置验收。自动任务不随装机启动。

应用来自官方网站；包清单与 [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile) 管理方式分开。记录实际版本和验收结果到新机本地，不把凭证、会话历史、进程环境或完整机器清单提交到仓库。
