# Shell 与技能链接维护

新版基础安装链接 `.zshrc`、`.zprofile`、`personal-apps` 命令、tmux、macOS iTerm Dynamic Profile 和选集中的 skills，默认恢复公开仓库的日常 shell 能力。Git 身份、SSH、应用登录、会话数据库与旧 plugin cache 不在安装范围内。`mac_install.sh` 是同一预览入口，不安装包、改登录 shell、拉子模块或覆盖配置。

## 安装与回滚

先从 [personal-mac profile](../profiles/personal-mac/README.md) 安装依赖。链接安装器需要 Python 3.9+，App 命令需要 Python 3.11+，profile 提供固定 Python 3.12；项目环境由 uv 管理。将 dotfiles 和 CS-Notes clone 到长期路径，不链接临时 worktree。

```sh
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes"
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes" --apply
```

冲突默认停止，且在写任何链接前检查整批目标。审查已有配置后，可增加 `--replace`：原文件、目录或 dangling symlink 都保留在 `~/.local/state/dotfiles/<transaction>/`。同目标重复执行不会重复备份。

安装器输出 `receipt` 的本机路径。用该实际路径预览回滚，再执行：

```sh
python3 tools/install.py --rollback /path/to/receipt.json
python3 tools/install.py --rollback /path/to/receipt.json --apply
```

回滚前检查整个批次仍指向本次源文件；被用户改成其他目标时停止，不覆盖新配置。回滚只移除本次链接并恢复原入口，保留仓库中的编辑和依赖包。不要运行来历不明或被修改的 receipt。

`--skills-only` / `--shell-only` 可缩小范围，`--no-preferences` 跳过 tmux/iTerm，`--skills-dir` 可指定客户端实际使用的发现目录。默认先拒绝不完整 / sparse checkout，再从 CS-Notes 的 `note-system/skills/manifest.json` 验证每个文件和摘要，链接整个技能目录。不要为同一个客户端在不同目录安装同名副本。修改已链接技能会直接修改仓库；公开前审查 diff 并刷新 manifest。链接后的 source 是可信执行输入，不自动拉取或自动发布变更。

## 配置加载与兼容

`zprofile` 只加载 PATH 和 `~/.zprofile.local`；`zshrc` 加载共享 PATH 与无启动子进程的 App 路由 functions，只有交互 shell 才加载补全、按键、插件与 prompt。新窗口自动加载；旧窗口 `source ~/.zshrc` 或 `dotfiles-reload` 刷新 alias、prompt 与私人 hook，不重复初始化插件；插件代码变化后开新 shell。非交互 Agent 显式 source 时得到 PATH 和路由，不注入插件输出。命令与上游二进制的区别见 [App 协同](../profiles/personal-mac/APP_WORKFLOW.md)。

PATH 保留已激活虚拟环境、版本管理器和已有命令的优先级，追加存在的通用用户工具路径。没有 Node 时才加入 Node 24 后备目录。默认不激活 Conda；需要时设置 `CONDA_HOME`，执行 `conda-init` 再激活环境。

旧机已有 `.aliases`、`.zshrc_local` 仍会加载；随后修复固定 Python/pip 与不正确引用路径的 fzf alias。新的私人扩展放在 `~/.config/personal/zshrc.local`，登录专用配置放在 `~/.zprofile.local`。替换旧 `.zprofile` 前将仍需要的个人配置合入本地 hook，备份不会自动执行。

不再 source Bash 的 profile；`mybin/` 进入 PATH，同时只加载已审查的 marco/polo、pidwait 和 debug 纯函数定义。移除重复插件管理、启动下载/更新检查、多个旧 Conda hook 和每次删除补全缓存。完整 Oh My Zsh Git lib/plugin 固定版本随 [vendor](../vendor/oh-my-zsh/README.md) 交付，补全后加载，无需启动整个框架。其余插件优先读取 Homebrew 安装文件，旧机可回退已安装的独立插件；缺失时 shell 仍可用，doctor 报告缺项。旧 submodules 保留为可选资产，基础安装不拉取整套 Vim/C++ 等依赖。fzf 由 Homebrew 维护；发现 Homebrew 版本后移除旧 `~/.fzf/bin` 的 PATH 项，旧副本保留但不参与新终端解析。

原公开插件清单中的 fzf、跳目录、补全、建议、高亮、历史搜索和 Git prompt 均默认提供；zplug 的包管理职责由固定源码与 Brewfile 接替，autojump 由 zoxide 提供兼容命令，zsh-git-prompt 的状态展示由公共 prompt 实现。不是只保留一小组 Git alias。额外纠错工具和 Vim/C++ 子模块按项目使用，不随 shell 启动自动安装。

补全只初始化一次，保留按 Zsh 版本区分的 dump，并继续检查目录权限。语法高亮最后加载，避免后定义的 widget 绕过它。官方依据：[Zsh compinit](https://zsh.sourceforge.io/Doc/Release/Completion-System.html#Use-of-compinit)、[高亮插件安装顺序](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md)。

## 直接可用的操作

| 操作 | 行为 |
| --- | --- |
| Tab | 常规补全与候选菜单 |
| Ctrl-R | 终端中使用 fzf 历史搜索；缺插件时回退内建搜索 |
| 上/下方向键 | 已加载 substring 插件时按当前输入搜索历史，否则按前缀搜索 |
| 右方向键 | 接受可用的 autosuggestion；Esc 保留 Vi 模式切换 |
| Ctrl-A / Ctrl-E | 插入模式回到行首/行尾 |
| `j <keyword>` | 优先 zoxide，旧机可回退已安装 autojump |
| `mkcd <path>` | 创建并进入目录，支持空格 |
| `vfzf` / `cdfzf` / `gitfzf` | 文件打开、目录选择、本地 Git 分支切换；取消不执行后续动作 |
| `gs` / `gd` / `gl` | 状态、diff、短日志 |
| `gco` / `gcb` / `gst` / `gss` | 完整 Git 插件：checkout、checkout -b、status、status --short |
| `marco` / `polo` / `pidwait` | 保存/返回目录、等待指定 PID |
| `set_my_env <label>` | 显示环境标签，不连接任何主机 |

默认分段 prompt 显示成功/失败、环境标签、虚拟环境、时间、目录和 Git 分支，包含 detached HEAD、ahead/behind、staged、unstaged、untracked 和冲突计数。每次 prompt 用一次只读 Git status，不调用 Python。`DOTFILES_GIT_PROMPT=0` 关闭查询；`DOTFILES_PROMPT_STYLE=compact` 去掉 Powerline 箭头。Meslo / Pastel 的 Dynamic Profile 与当前会话字体刷新见 [第一阶段流程](../profiles/personal-mac/SETUP_STEP1.md)。

## 验收

```sh
python3.12 -m unittest discover -s tests -v
zsh -ic dotfiles-doctor
python3 tools/benchmark-shell.py --repeat 5
```

doctor 在无终端行编辑器时跳过 fzf widget；真实快捷键需在新终端验证。计时仅保存秒数、退出码和输出字节数，不记录环境或启动文本。冷启动与热启动分开理解，不把某台机器的测量当作所有机器的承诺。

在新终端实际检查 Tab、Ctrl-R、方向键、灰色建议和语法高亮；激活项目 venv 后确认 `command -v python` 指向该环境。用 `j` 进入一个此前访问过的临时目录；首次访问没有历史时不算失效。打开新 Agent 子进程验证 PATH，避免仅当前终端可用。`DOTFILES_SKIP_LOCAL=1 zsh -ic dotfiles-doctor` 可隔离本地 hook 的影响。
