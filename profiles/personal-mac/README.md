# Personal Mac profile

面向 Apple Silicon 的精简开发配置，适合从公开资料重建个人电脑。此目录独立使用，不调用仓库根目录的历史 `bootstrap.sh` / `mac_install.sh`，也不读取旧 SSH、账号或设备配置。

## 安装与验收

先在新机完成 [Xcode Command Line Tools 与 Homebrew](https://docs.brew.sh/Installation)，再从本仓库根目录执行：

```sh
brew bundle install --file profiles/personal-mac/Brewfile --no-upgrade
```

`node@24` 的 bin 目录需进入 PATH。对照 `zshrc.example` 合并必要配置，保留已有文件并做本机备份；登录 shell 的 Homebrew 初始化遵循安装器输出。不要覆盖配置，不运行 `brew bundle cleanup`。

Python 使用 `uv python install 3.12` 和项目独立虚拟环境。Node 默认一套 24 LTS，仓库另有要求时按仓库锁文件/版本约束安装；不要把某个 App 自带的 Node、Python、pnpm 路径当成系统依赖。Rust、Go、pnpm、容器和 OCR 等按实际项目安装。

`gitconfig.example` 不含身份信息；本人在新机设置 Git 名称和邮箱，GitHub 认证在新机进行。凭证、SSH 私钥和账号配置不放进这个 profile。

```sh
bash profiles/personal-mac/verify.sh
brew bundle check --file profiles/personal-mac/Brewfile
```

检查脚本只读，不登录、不联网、不启动服务。`Brewfile.optional` 是按需索引；若只需 PDF 提取，安装 `poppler` 即可，不必整份安装。

## 图形软件与长期维护

先读 [软件与偏好清单](./SOFTWARE.md)，核对已有软件、根 README 的历史偏好和新机用途。选定的 GUI 起步清单独立放在 `Brewfile.apps`，包括 iTerm2、Typora、Chrome、The Unarchiver 与 KeepingYouAwake：

```sh
brew bundle install --file profiles/personal-mac/Brewfile.apps --no-upgrade
```

桌面 Agent 客户端与一个主编辑器从官方入口安装，登录与许可证由本人处理。Mendeley、CodexBar、CC Switch、办公 / 日常应用按清单逐项决定；完成报告必须记录安装、暂缓及设置验收。模型服务、容器 VM 和自动任务不随装机自动启动。

应用来自官方网站；包清单与 [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile) 管理方式分开。记录实际版本和验收结果到新机本地，不把凭证、会话历史、进程环境或完整机器清单提交到仓库。
