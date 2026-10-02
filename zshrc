# Resolve this file through its symlink so the checkout can live anywhere.
typeset -g DOTFILES_ROOT="${${(%):-%N}:A:h}"
source "$DOTFILES_ROOT/shell/zshrc.zsh"
