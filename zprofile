typeset -g DOTFILES_ROOT="${${(%):-%N}:A:h}"
source "$DOTFILES_ROOT/shell/path.zsh"
[[ -r "$HOME/.zprofile.local" ]] && source "$HOME/.zprofile.local"

return 0
