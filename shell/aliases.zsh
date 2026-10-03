alias ll='ls -aGhlt'
alias la='ls -a'
alias l='ls -CF'
alias v='vim'
alias cls='clear'
alias dc='cd'
alias gs='git status'
alias gc='git commit'
alias gqa='git add .'
alias glast='git show HEAD'
alias gclean='git reset --hard && git clean -dfx'
alias gd='git diff'
alias gl='git log --oneline --decorate -15'
alias gch='git cherry-pick'
alias mv='mv -i' mkdir='mkdir -p' df='df -h' sudo='sudo '
alias dkst='docker stats'
alias dkps='docker ps'
alias dklog='docker logs'
alias dkpsa='docker ps -a' dkimgs='docker images'
alias dkcpup='docker compose up -d'
alias dkcpdown='docker compose down'
alias dkcpstart='docker compose start' dkcpstop='docker compose stop'
alias zshconfig='${EDITOR:-vim} "$HOME/.config/personal/zshrc.local"'
alias fdrecent="fd . -0 -t f | xargs -0 stat -f '%m%t%Sm %N' | sort -n | cut -f2- | tail -n 1"
alias grepctx='grep -r -n -C 3 --color=auto'
alias calc_csv_avg='python3 "$DOTFILES_ROOT/dotfile_tools/calc_csv_avg.py"'

source "$DOTFILES_ROOT/mybin/marco.sh"
source "$DOTFILES_ROOT/mybin/pidwait.sh"
source "$DOTFILES_ROOT/mybin/debug.sh"
# Compatibility entry point for tools that queried autojump directly.
function autojump { command zoxide query "$@"; }
function condai { (( $+commands[conda] )) || conda-init || return; command conda "$@"; }

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
