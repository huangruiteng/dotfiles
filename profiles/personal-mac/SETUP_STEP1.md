# 第一阶段装机与验收

第一步交付可直接使用的个人工作环境：完整的公开仓库、11 个审查过的技能入口、基础工具、完整 Git alias 与通用 shell helper、分段 Git prompt、Meslo / Pastel 终端，以及能实际请求的 Agent 和浏览器。分别记录“已安装、已配置、GUI 已验收、真实请求已通过”，不能用安装命令退出成功替代使用验收。

本阶段不安装、更新或启动 LoopX runtime，不恢复 Goal、Todo、SQLite、核心角色、Finance 或 Decision 状态，不创建长期自动化。历史文档中的 LoopX 入口不属于本阶段安装任务。登录、系统许可、条款与购买由本人处理；缺 key、许可证或网络订阅时继续独立项目。

## 材料、来源与网络

1. 先校验交付压缩包的 SHA256，再按包内说明运行 `python3 -B verify_environment.py`，通过后阅读交接、个人背景、软件偏好与网络说明。校验失败先查文件，不修改期望摘要以求通过。
2. 只用此次审查过的公开资料。安装前回到厂商官网、官方仓库或 Homebrew 官方 formula/cask 核对当前支持；盘点已有应用和版本再补缺。
3. 用有界请求分别检查 GitHub、Homebrew 下载源、模型 API 和日常公开网页，记录状态、耗时与失败类型。代理配置和订阅地址只留本机；不关闭 TLS 校验、不复制旧身份，也不同时运行多个安装器。
4. Homebrew clone 慢或中断时，先检查 `/opt/homebrew/bin/brew` 和安装进程，再按 [官方安装说明](https://docs.brew.sh/Installation) 恢复。`brew: command not found` 也可能是 PATH 尚未加载。需要 sudo 时由本人输入密码；不要为提速直接执行陌生镜像脚本。

## 完整 checkout，再建立链接

dotfiles 和 CS-Notes 放入长期目录，不能用只含 `note-system` 的交接导出目录冒充完整 checkout。先检查现有仓库的状态、来源和提交；不对已有改动执行强制 checkout、reset 或 clean。新的空目录可按以下方式取得已审查的提交，变量必须来自此次交接中的完整 commit：

```sh
git clone --depth 1 --no-checkout https://github.com/huangrt01/dotfiles.git "$HOME/Developer/dotfiles"
git -C "$HOME/Developer/dotfiles" fetch --depth 1 origin "$DOTFILES_COMMIT"
git -C "$HOME/Developer/dotfiles" checkout --detach FETCH_HEAD
git clone --depth 1 --no-checkout https://github.com/huangrt01/CS-Notes.git "$HOME/Developer/CS-Notes"
git -C "$HOME/Developer/CS-Notes" fetch --depth 1 origin "$NOTES_COMMIT"
git -C "$HOME/Developer/CS-Notes" checkout --detach FETCH_HEAD
```

核对最终 `HEAD` 等于各自审查提交，再从 dotfiles 根目录检查：

```sh
python3 tools/check_checkout.py "$HOME/Developer/dotfiles"
python3 tools/check_checkout.py "$HOME/Developer/CS-Notes"
```

检查器拒绝 sparse checkout、缺少的索引文件和错误文件类型，单列旧外部 symlink 的断链；未初始化的历史 submodule 单独计数，基础 shell 不依赖它们。它检查完整性，不验证来源或改动是否经过审查。bootstrap 默认执行同一检查；`--allow-export` 只适用于另外审查过的非 Git 导出，不能证明 checkout 完整。

## Shell、字体与技能

```sh
brew bundle install --file profiles/personal-mac/Brewfile --no-upgrade
brew bundle install --file profiles/personal-mac/Brewfile.apps --no-upgrade
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes"
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes" --apply
```

先读预览；冲突不会覆盖。需要替换时审查后加 `--replace`，保存返回的 receipt。默认链接 shell、App 路由、tmux、iTerm Dynamic Profile 和 manifest 中的 11 个 skills；`--no-preferences` 可跳过 tmux/iTerm。依赖安装不会执行 cleanup 或启动服务。

公开 shell 默认加载完整的 Oh My Zsh Git lib/plugin、补全、fzf、zoxide、autosuggestions、history substring search 和 syntax highlighting，恢复 `gco`、`gcb`、`gst`、`gss`、marco/polo、pidwait 等通用能力。代码固定版本随仓库交付，启动不下载插件，不启动旧 zplug 更新器。破坏性 Git helper 仅由用户显式调用。

新窗口自动加载；旧窗口执行 `source ~/.zshrc` 或 `dotfiles-reload` 刷新 alias、prompt 与私人 hook，不重复初始化插件。插件本身的代码变化用新 shell 验证。私人 hook 保留身份、代理和个人覆盖，通用修复先进入公开源码；替换临时私人 workaround 前备份，仅移除已迁回公共模块的 source 行。

iTerm 默认使用 **Dotfiles Meslo Pastel**，普通字体和非 ASCII 字体均为 MesloLGSNFM-Regular 14，黑底 Pastel 配色，回看上限 10000 行。profile 不含旧主机、启动命令或环境。按 [iTerm 官方 Dynamic Profiles](https://iterm2.com/documentation-dynamic-profiles.html) 交付；当前会话通过 [官方 OSC 接口](https://iterm2.com/documentation-escape-codes.html) 刷新字体。已手动安装同一官方字体时先验证，避免只为 cask 登记重复安装。可设置 `DOTFILES_ITERM_APPEARANCE=0` 保留自己的 profile，或 `DOTFILES_PROMPT_STYLE=compact` 使用不含 Powerline 箭头的 prompt。

```sh
swift tools/check-font.swift
bash profiles/personal-mac/verify.sh
zsh -ic dotfiles-doctor
python3.12 -m unittest discover -s tests -v
python3 tools/benchmark-shell.py --repeat 5
```

字体存在还不等于当前窗口已换字体。在真实新终端查看箭头和 Git 图标，再验证 `gco`、分支、detached HEAD、dirty 状态、Tab、Ctrl-R、方向键、灰色建议和语法高亮。激活项目 venv 后确认 Python 路径，再从 Finder / Agent 新进程检查工具 PATH。补全缓存可因目录权限审计重新生成，不要求 mtime 永不变化，不绕过权限审计来缩短计时。

11 个技能必须从长期 CS-Notes checkout symlink，manifest 文件集与 SHA256 均通过。分别检查 GPT、DS 客户端发现并启用它们，再执行至少一个合适的技能任务；只有目录数量不足以证明可用。额外的官方 Ego / Lark 技能记录来源版本，不覆盖这 11 个入口。

## Markdown 阅读器：以 Command + 左键实测

先检查路径，再检查阅读器：

```sh
python3 tools/check_markdown.py "$HOME/Developer/CS-Notes/README.md"
python3 tools/check_markdown.py profiles/personal-mac/smoke/reading.md
```

检查器按源文件所在目录解析常见本地链接，处理中文、空格与 URL 编码，跳过外链和代码示例。`ui_verified` 始终为 false：文件存在不证明阅读器能跳转、渲染或定位 anchor，也不宣称完整覆盖 CommonMark 语法。

在候选阅读器打开 [验收页](./smoke/reading.md)，实际用 **Command + 左键** 点击中文路径、带空格路径、编码路径，检查目标正文标记，返回后再次跳转；再测 CS-Notes 中 `Notes/云原生-ToB.md` 和 `Learning-Materials/README.md`。同时查看公式、相对 SVG 图片、表格 `<br>` 与 Mermaid 的显示情况，记录不支持项。

只有核心阅读和跳转通过，才设置 `.md` 默认关联，再用 Finder 双击与 `open` 验证关联确实生效。失败时保留候选为试用或恢复前一个阅读器；不批量改写笔记掩盖阅读器 bug。ColaMD 须按相同流程评估，不能因为启动成功就取代 Typora。许可证与购买由本人完成。

## Agent、Ego 与飞书

按 [App 协同](./APP_WORKFLOW.md) 初始化独立 GPT / DS home。本人在 GPT 窗口登录并选择可用模型，在本机编辑权限 600 的 DS 配置，不在聊天或参数中发送 key。两边各完成一个有界真实请求，验证实际模型与状态目录，再重复调用开窗命令确认聚焦同一进程。Finder 不读取 zprofile，需测试新启动进程的 PATH；官方 App 已提供可用 CLI 时先核对已有入口，避免重复安装一份 CLI。

Ego 必须完成一次公开页面操作和 TaskSpace 收尾 `finish({keep: []})`；App 已打开不等于浏览器集成可用。Typora 试用或激活状态、默认关联和实际阅读验证分别记录。

用户明确需要飞书时，安装 [官方 lark-cli](https://github.com/larksuite/cli)，校验发行 checksum，完成本机应用配置与用户授权。应用凭证就绪或 bot 可用不等于已连上本人的资源；必须检查 user 身份。权限按实际需求申请，基础连接不直接申请所有业务域。

```sh
lark-cli auth login --scope offline_access --no-wait --json
# 本人完成新页面授权后，Agent 使用本次响应的 device_code 完成登录。
# device_code 与原始 JSON 只存本机权限 600 文件，不进入公开文档或提交。
python3 tools/check_lark_auth.py
```

split flow 要将本次原始 URL 和二维码及时交给本人，并在本人回复后完成本次轮询；过期后重新发起，不继续点击旧页面。登录原始 JSON 由 Agent 捕获到本机权限 600 文件，不原样打印。`check_lark_auth.py` 调用官方 `auth status --json --verify`，真实请求服务端身份接口，只输出 user / token / verified 的布尔检查，bot 可用不会误判为连接本人成功；兼容性按 v1.0.97 的输出契约验证。报告不输出姓名、ID、token 或完整配置。页面出现 20001 / 请求不合法时分别检查有效期、当前会话、应用与身份，不盲目扩大权限，也不未经证据声称某个参数能修复。后续访问文档、日历等业务资源时再按缺失权限增量授权。

## 报告与撤销

本机报告记录软件取舍、官方来源、版本、完整 checkout、shell 与技能验证、GUI 跳转、真实请求、网络结果、备份 / receipt 及必要人手动作；不把整份机器报告、身份配置、凭证或私人截图提交公开仓库。明确写“第二步尚未开始”。

源码修改先看 Git diff；链接按实际 receipt 预览回滚，再 `--apply`。依赖和已经使用的 App 数据不随链接回滚删除。迁回公开模块的私人 workaround 保留备份，恢复时先撤销对应公开改动，避免重复加载。Lark 本机 logout、删除安装文件、服务端撤销授权是不同操作，不能互相冒充。不要清空承载登录或历史数据的 home。
