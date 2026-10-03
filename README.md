## dotfiles

个人 Apple Silicon 新机从 [第一阶段装机与验收](profiles/personal-mac/SETUP_STEP1.md) 和 [personal-mac profile](profiles/personal-mac/README.md) 开始。默认延续完整 Git alias、通用 shell helper、fzf / 跳目录 / 建议 / 高亮，以及 Meslo / Pastel 分段 Git prompt；完整 checkout 和真实使用验收是交付条件。[软件与偏好清单](profiles/personal-mac/SOFTWARE.md) 和 [App 协同](profiles/personal-mac/APP_WORKFLOW.md) 提供 Codex GPT/DS、Ego Lite、Typora 的选择与入口。第一步不安装或启动 LoopX runtime，不迁移旧状态。预览式 `bootstrap.sh --skills-repo <CS-Notes checkout>` 统一链接 shell、终端偏好、App 命令和公开 skills，显式 `--apply` 才写入。详见 [shell、快捷键与回滚](docs/SHELL.md)。下文保留历史软件偏好，不作为批量安装命令。

### 从零搭建工作环境

* Macbook
  * 触控板：轻点

* 飞书、飞连

* 个人git仓库：

  * Dotfiles、CS-Notes

  * Dotfiles-local

    * 配置ssh + git账号
    * `git clone git@github.com:huangrt01/dotfiles-local.git`

  * ```shell
    git config --global user.name "huangrt01"
    git config --global user.email huangrt01@163.com
    
    # MacOs
    ssh-keygen -t rsa -b 4096 -C "huangrt01@163.com" # 如果rsa已占用，可用ssh-keygen -t ed25519 -C "huangruiteng@xxx.com"
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/id_rsa --apple-use-keychain # MacOS带
    pbcopy < ~/.ssh/id_rsa.pub  # MacOS , Linux用xclip
    
    上github添加SSH Key
    
    ssh -T git@github.com
    # ssh-keygen -y -f ~/.ssh/id_rsa
    
    # Linux
    ```

* Iterm2、Sublime text
  * enter iTerm2/Settings
    * Profiles/Text/Font -> Meslo*
    * Profiles/Colors/ColorPresets -> Pastel*
  * Unlimited scroll back 

* Chrome

  * 账号

* Typora

  * 序列号
  * ![image-20250319230752532](./README/image-20250319230752532.png)
  * 内联公式开启

* 豆包、微信、网易云音乐

* Clion、VSCode、Trae

* Mendeley
  * https://www.mendeley.com/download-reference-manager/macOS

* QuickJump

* MailMaster, WeChat

* 解压缩 https://theunarchiver.com/

* Discord



* 暂时搁置

  * [hammerspoon](https://github.com/Hammerspoon/hammerspoon)

  * [Karabiner-Elements](https://karabiner-elements.pqrs.org/)

### dotfile

* my dotfiles, the design philosophy is illustrated in my [Shell Note](https://github.com/huangrt01/CS-Notes/blob/master/Notes/Output/Shell-MIT-6-NULL.md)
* easy-to-use
```shell
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes"
# 核对预览后执行；已有文件冲突需先审查并选择 --replace 备份。
sh bootstrap.sh --skills-repo "$HOME/Developer/CS-Notes" --apply
```

#### submodules
* zsh plugins: [zplug](https://github.com/zplug/zplug), [fzf](https://github.com/junegunn/fzf), [autojump](https://github.com/wting/autojump.git), [zsh-completions](https://github.com/zsh-users/zsh-completions), [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions), [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting), [zsh-history-substring-search](https://github.com/zsh-users/zsh-history-substring-search), [zsh-git-prompt](https://github.com/olivierverdier/zsh-git-prompt)
* vim plugins：[ack.vim](https://github.com/mileszs/ack.vim), [ctrlp.vim](https://github.com/ctrlpvim/ctrlp.vim), [nerdtree](https://github.com/preservim/nerdtree), [vim-fugitive](https://github.com/tpope/vim-fugitive), [vim-rhubarb](https://github.com/tpope/vim-rhubarb), [ale](https://github.com/dense-analysis/ales)
* `shallow=true'

#### local customization
* shell
```shell
if [ -f ~/.zshrc_local ]; then
    source ~/.zshrc_local
fi
```

* git
```shell
[include]
        path = ~/.gitconfig_local
```
* vim
```shell
let $LOCALFILE=expand("~/.vimrc_local")
if filereadable($LOCALFILE)
    source $LOCALFILE
endif
```
* tmux
```shell
if-shell "[ -f ~/.tmux_local.conf ]" 'source ~/.tmux_local.conf'
```

#### Manually install (apt/pip)

* vim-ale related: [shellcheck](https://github.com/koalaman/shellcheck), [write-good](https://github.com/btford/write-good)(or [proselint](http://proselint.com/) )

```shell
apt install shellcheck
npm install -g write-good
```

* [tldr](https://tldr.sh/), fd, rg, [mosh](https://mosh.org/#getting), [tree](http://mama.indstate.edu/users/ice/tree/), ag

```shell
# apt install silversearcher-ag
git clone https://github.com/satanson/the_silver_searcher.git --depth=1
sudo apt install -y automake pkg-config libpcre3-dev zlib1g-dev liblzma-dev
./build.sh
sudo make install

apt install tree

# https://nodejs.org/en/download/package-manager/#installing-node-js-via-package-manager
npm install -g tldr

apt install fd-find
apt install cloc
```

* [hub](https://github.com/github/hub)([usage](https://hub.github.com/#developer)), tig
* [Valgrind](https://valgrind.org/), Perf, stress, [rr](https://rr-project.org/), htop

```shell
sudo apt-get update
pip3 install --upgrade pip

sudo apt install zsh
zsh --version

# log out and login back
echo $SHELL
$SHELL --version

sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

sudo apt-get install python3-pip
pip install --upgrade pip
pip install --upgrade setuptools
pip install ipython
pip install ipdb
pip3 install thefuck

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple virtualenvwrapper
export WORKON_HOME=~/Envs
mkdir -p $WORKON_HOME
source /usr/local/bin/virtualenvwrapper.sh
# or
source ~/.local/bin/virtualenvwrapper.sh

# install perf
sudo apt install linux-source
cd /usr/src
tar -xjf linux-source-4.4.0.tar.bz2
cd tools/perf
make # fail! why?
sudo apt install linux-tools-common

perf
# ...
# follow the instructions
# ...
# finish installing perf

apt install stress
apt install htop
```

* python3, pip3, ipython, ipdb
  * Pip3:  [line_profiler](https://github.com/pyutils/line_profiler), [memory-profiler](https://pypi.org/project/memory-profiler/), [pycallgraph](http://pycallgraph.slowchop.com/en/master/)
```
pip install pycallgraph, tabulate, line_profiler, memory-profiler
pip3 install openai
apt install graphviz
# dot -v
```

**Security**:

* [gpg](https://www.digitalocean.com/community/tutorials/how-to-use-gpg-to-encrypt-and-sign-messages), [haveged](https://www.digitalocean.com/community/tutorials/how-to-setup-additional-entropy-for-cloud-servers-using-haveged)

**Firefox Add-on**

* HTTPS Everywhere, Multi-Account Containers(No Chrome), [uBlock Origin](https://github.com/gorhill/uBlock), 1Password

* [stylus](https://github.com/openstyles/stylus/)
* Full Web Page Screenshots (Chrome: Full Page Screen Capture



### Linux

```
apt update
apt install gdb manpages-dev file sysstat
```

#### X11 Forwarding

https://blog.wangluyuan.cc/2020/12/24/forwarding-x11/



### Macbook

* 自动化：
  * 安装brew
  * 下载安装powerline font

### Trae

#### 插件

* GitLens
* basedpyright
* python

### Clion

* git插件生效
  * `git config --global --add safe.directory /root/newrec/huangruiteng/tiger_team`

* yapf format
  * ![image-20250401162909307](./README/image-20250401162909307.png)
  * 需要重启IDE才能在KeyMap里看到



### VSCode

#### 开发必备插件

* 公共: 
  * Python
  * Remote - SSH
  * **ByteDance Authenticator**
  * MarsCode
  * GitLens
  * Code Spell Checker, EditorConfig for VSCode, String Manipulation, Visual Studio IntelliCode
  * Code Runner
* Python:
  * Python
  * yapf
    * 添加settings.json
* C++: [cpplint](https://github.com/cpplint/cpplint), CodeLLDB, Header source switch, Rainbow Brackets, C++ Intellisense
  * CMake, CMake Tools
    * cmake插件需要cmake3.9.4以上版本的cmake的支持，ubuntu16.04以下的用户可能需要手动安装新版本的cmake
  * Clangd
    * [VSCode C/C++ 开发环境和调试配置：Clangd+Codelldb](https://zhangjk98.xyz/vscode-c-and-cpp-develop-and-debug-setting/)
      * 阅读超大型项目源码的注意事项
        * 关闭 editor.formatOnSave, clang-tidy, all-scopes-completion
        * codeLLDB 使用（TODO）

    * 有clangd之后，不需要 C/C++ (by Microsoft) 了

  * Tabnine：AI加持的自动补全，用GPT
  * Peacock：不同workspace可以用不同的颜色区分
  * 调大C++插件的可用内存：
    * ![c++](./README/vscode-c++.png)
  * [如何优雅的用 VScode 编写 C++ 大型项目？](https://www.zhihu.com/question/353722203/answer/2564104885)
    * lsp(language service provider): vscode clangd
    * 依赖 compile_commands.json
      * 自动构建
      * 手动生成：`mkdir build && cd build && cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=1 ..`
    * 如果linux的glibc版本较旧，需要给clangd打补丁（patchelf），链接向新版glibc

### Reference

* 可以参考：https://github.com/AnswerDotAI/fastsetup
