alias ll='ls -lah'
alias la='ls -a'
alias v='vim'
alias cls='clear'
alias gs='git status --short --branch'
alias gd='git diff'
alias gl='git log --oneline --decorate -15'
alias gch='git cherry-pick'
alias dkps='docker ps'
alias dklog='docker logs'
alias dkcpup='docker compose up -d'
alias dkcpdown='docker compose down'

# Never mask an activated Python environment with an absolute interpreter alias.
(( $+commands[python] )) || alias python=python3
mkcd() { [[ $# == 1 ]] || return 2; command mkdir -p -- "$1" && builtin cd -- "$1"; }
vfzf() {
  local selected
  selected=$(fzf --query="${1:-}") || return
  [[ -n "$selected" ]] && "${EDITOR:-vim}" -- "$selected"
}
cdfzf() {
  local selected
  selected=$(command find . -type d -not -path './.git/*' -print | fzf --query="${1:-}") || return
  [[ -n "$selected" ]] && builtin cd -- "$selected"
}
gitfzf() {
  local selected
  selected=$(command git for-each-ref --format='%(refname:short)' refs/heads | fzf) || return
  [[ -n "$selected" ]] && command git switch -- "$selected"
}
# Opt-in Conda activation; starting a terminal never activates base.
conda-init() {
  local base
  for base in "${CONDA_HOME:-}" "$HOME/miniconda3" "$HOME/anaconda3" /opt/miniconda3 /opt/anaconda3; do
    [[ -n "$base" && -r "$base/etc/profile.d/conda.sh" ]] || continue
    source "$base/etc/profile.d/conda.sh"
    return
  done
  print -u2 'Set CONDA_HOME to an installed Conda prefix.'
  return 1
}
