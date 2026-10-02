# Routing functions also work when agents explicitly source ~/.zshrc.
# The upstream executable remains available through `command codex`.
_dotfiles_apps() { "$DOTFILES_ROOT/tools/personal-apps" "$@"; }
codex() {
  case "${1:-}" in
    app) shift; _dotfiles_apps open gpt "$@" ;;
    ds)
      shift
      if [[ ${1:-} == app ]]; then shift; _dotfiles_apps open ds "$@"
      else _dotfiles_apps cli ds -- "$@"; fi ;;
    --native) shift; command codex "$@" ;;
    secondary) print -u2 'This profile provides GPT and DS routes only.'; return 2 ;;
    *) _dotfiles_apps cli gpt -- "$@" ;;
  esac
}
cxgpt() { _dotfiles_apps cli gpt -- "$@"; }
cxa() { cxgpt "$@"; }
cxds() { _dotfiles_apps cli ds -- "$@"; }
loopx() {
  if [[ ${1:-} == app ]]; then shift; _dotfiles_apps open loopx "$@"
  else command loopx "$@"; fi
}
ego() {
  [[ ${1:-} == lite ]] && shift
  if [[ ${1:-} == app ]]; then shift; _dotfiles_apps open ego "$@"
  else print -u2 'Use ego app (or ego lite app); browser automation uses ego-browser.'; return 2; fi
}
typora() {
  [[ ${1:-} == app ]] && shift
  _dotfiles_apps open typora "$@"
}
