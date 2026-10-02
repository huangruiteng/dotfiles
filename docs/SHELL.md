# Shell 与技能链接维护

新版基础安装只链接 `.zshrc`、`.zprofile` 和选集中的 skills。Git 身份、SSH、应用登录、会话数据库与旧 plugin cache 不在安装范围内。`mac_install.sh` 是同一预览入口的兼容包装，不再安装包、改登录 shell、递归拉子模块或覆盖配置。

## 安装与回滚

先从 [personal-mac profile](../profiles/personal-mac/README.md) 安装基础依赖。需要 Python 3.9+；profile 推荐 uv 管理的 Python。将 dotfiles 和 CS-Notes clone 到长期维护的路径，不要链接临时 worktree。

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

`--skills-only` / `--shell-only` 可缩小范围，`--skills-dir` 可指定客户端实际使用的发现目录。不要为同一个客户端在不同目录安装同名副本。默认从 CS-Notes 的 `note-system/skills/manifest.json` 验证每个文件和摘要，再链接整个技能目录。修改已链接技能会直接修改仓库；公开前审查 diff 并刷新 manifest。链接后的 source 是可信执行输入，不自动拉取或自动发布变更。

## 配置加载与兼容

`zprofile` 只加载 PATH 和 `~/.zprofile.local`；`zshrc` 加载共享 PATH，只有交互 shell 才加载补全、按键、插件与 prompt。重复 source 不重复初始化；更改插件配置后开新 shell。非交互 Agent 显式 source 时只得到 PATH，不注入插件输出。

PATH 保留已激活虚拟环境、版本管理器和已有命令的优先级，追加存在的通用用户工具路径。没有 Node 时才加入 Node 24 后备目录。默认不激活 Conda；需要时设置 `CONDA_HOME`，执行 `conda-init` 再激活环境。

旧机已有 `.aliases`、`.zshrc_local` 仍会加载；随后修复固定 Python/pip 与不正确引用路径的 fzf alias。新的私人扩展放在 `~/.config/personal/zshrc.local`，登录专用配置放在 `~/.zprofile.local`。替换旧 `.zprofile` 前将仍需要的个人配置合入本地 hook，备份不会自动执行。

不再 source Bash 的 profile，也不逐个 source `mybin/` 下的脚本；该目录只进入 PATH。移除重复插件管理、启动下载/更新检查、多个旧 Conda hook 和每次删除补全缓存。插件优先读取 Homebrew 安装文件，旧机可回退已安装的独立插件；缺失时 shell 仍可用，doctor 报告缺项。旧 submodules 保留为可选资产，基础安装不拉取整套 Vim/C++ 等依赖。

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
| `set_my_env <label>` | 显示环境标签，不连接任何主机 |

prompt 显示退出码、环境标签、虚拟环境、目录和 Git 分支，默认不遍历仓库计算 dirty 状态，也不调用 Python。`DOTFILES_GIT_PROMPT=0` 可关闭分支查询；`gs` 查看完整状态。旧主题、纠错工具和大批 shell 插件不随启动自动恢复，确有用途时单独加。

## 验收

```sh
python3 -m unittest discover -s tests -v
zsh -ic dotfiles-doctor
python3 tools/benchmark-shell.py --repeat 5
```

doctor 在无终端行编辑器时跳过 fzf widget；真实快捷键需在新终端验证。计时仅保存秒数、退出码和输出字节数，不记录环境或启动文本。冷启动与热启动分开理解，不把某台机器的测量当作所有机器的承诺。

在新终端实际检查 Tab、Ctrl-R、方向键、灰色建议和语法高亮；激活项目 venv 后确认 `command -v python` 指向该环境。用 `j` 进入一个此前访问过的临时目录；首次访问没有历史时不算失效。打开新 Agent 子进程验证 PATH，避免仅当前终端可用。`DOTFILES_SKIP_LOCAL=1 zsh -ic dotfiles-doctor` 可隔离本地 hook 的影响。
