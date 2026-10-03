# Full Git aliases/functions without an Oh My Zsh runtime or startup updater.
if [[ ${_DOTFILES_GIT_LOADED:-0} != 1 ]] && (( $+commands[git] )); then
  # The standalone library has no OMZ async runtime to register handlers with.
  zstyle ':omz:alpha:lib:git' async-prompt false
  source "$DOTFILES_ROOT/vendor/oh-my-zsh/git.zsh"
  source "$DOTFILES_ROOT/vendor/oh-my-zsh/git.plugin.zsh"
  typeset -g _DOTFILES_GIT_LOADED=1
fi

# Helpers used by the Git plugin, evaluated only when explicitly called.
clipcopy() {
  if (( $+commands[pbcopy] )); then
    if (( $# )); then command pbcopy < "$1"; else command pbcopy; fi
  elif (( $+commands[xclip] )); then
    if (( $# )); then command xclip -selection clipboard < "$1"; else command xclip -selection clipboard; fi
  else
    print -u2 'Install a clipboard utility before using this Git helper.'; return 1
  fi
}
clippaste() {
  if (( $+commands[pbpaste] )); then command pbpaste
  elif (( $+commands[xclip] )); then command xclip -selection clipboard -o
  else print -u2 'Install a clipboard utility before using this Git helper.'; return 1; fi
}
