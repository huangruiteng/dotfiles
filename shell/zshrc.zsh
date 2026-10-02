source "$DOTFILES_ROOT/shell/path.zsh"
# Explicit sourcing in an agent's non-interactive shell loads PATH only.
[[ -o interactive ]] || return 0
[[ ${_DOTFILES_SHELL_LOADED:-} == 1 ]] && return 0
typeset -g _DOTFILES_SHELL_LOADED=1

HISTFILE=${HISTFILE:-$HOME/.zsh_history}
HISTSIZE=50000
SAVEHIST=50000
setopt APPEND_HISTORY INC_APPEND_HISTORY HIST_IGNORE_SPACE HIST_IGNORE_ALL_DUPS
setopt AUTO_CD INTERACTIVE_COMMENTS
export EDITOR=${EDITOR:-vim}
export CLICOLOR=1
[[ -t 0 ]] && export GPG_TTY=$TTY

# Resolve installed plugins without invoking brew or a second plugin manager.
_dotfiles_plugin_file() {
  local name=$1 file=$2 candidate
  for candidate in "/opt/homebrew/share/$name/$file" "/usr/local/share/$name/$file" \
      "$DOTFILES_ROOT/oh-my-zsh/custom/plugins/$name/$file" \
      "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/$name/$file"; do
    [[ -r "$candidate" ]] && { REPLY=$candidate; return 0; }
  done
  return 1
}
typeset -U fpath
for _df_dir in /opt/homebrew/share/zsh/site-functions /usr/local/share/zsh/site-functions \
    "$DOTFILES_ROOT/oh-my-zsh/custom/plugins/zsh-completions/src" \
    "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-completions/src"; do
  [[ -d "$_df_dir" ]] && fpath=("$_df_dir" $fpath)
done
unset _df_dir
# Retain the dump; compinit still audits permissions and detects new completions.
autoload -Uz compinit
compinit -i -d "${ZDOTDIR:-$HOME}/.zcompdump-$ZSH_VERSION"
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

# Vi editing with standard insertion shortcuts; ESC delay is in hundredths of a second.
bindkey -v
KEYTIMEOUT=10
bindkey -M viins '^A' beginning-of-line
bindkey -M viins '^E' end-of-line
bindkey -M viins '^R' history-incremental-search-backward
bindkey -M viins '^?' backward-delete-char
bindkey -M viins '^[[A' history-beginning-search-backward
bindkey -M viins '^[[B' history-beginning-search-forward
bindkey -M viins '^[OA' history-beginning-search-backward
bindkey -M viins '^[OB' history-beginning-search-forward

# Old machine aliases are optional; remove only the known broken overrides below.
[[ ${DOTFILES_SKIP_LOCAL:-0} != 1 && -r "$HOME/.aliases" ]] && source "$HOME/.aliases"
unalias python pip pip3 vfzf cdfzf gitfzf 2>/dev/null
source "$DOTFILES_ROOT/shell/aliases.zsh"
if _dotfiles_plugin_file zsh-autosuggestions zsh-autosuggestions.zsh; then source "$REPLY"; fi
if _dotfiles_plugin_file zsh-history-substring-search zsh-history-substring-search.zsh; then
  source "$REPLY"
  for _df_map in viins emacs; do
    bindkey -M "$_df_map" '^[[A' history-substring-search-up
    bindkey -M "$_df_map" '^[[B' history-substring-search-down
    bindkey -M "$_df_map" '^[OA' history-substring-search-up
    bindkey -M "$_df_map" '^[OB' history-substring-search-down
  done
  unset _df_map
fi
# Installed shell scripts work with old fzf versions too; no `fzf --zsh` version assumption.
if [[ -o zle && -t 0 && -t 1 ]]; then
for _df_fzf in /opt/homebrew/opt/fzf/shell /usr/local/opt/fzf/shell "$DOTFILES_ROOT/fzf/shell" "$HOME/.fzf/shell"; do
  [[ -r "$_df_fzf/key-bindings.zsh" ]] || continue
  [[ -r "$_df_fzf/completion.zsh" ]] && source "$_df_fzf/completion.zsh"
  source "$_df_fzf/key-bindings.zsh"
  break
done
unset _df_fzf
fi
if (( $+commands[zoxide] )); then
  eval "$(command zoxide init zsh --cmd j)"
else
  for _df_jump in /opt/homebrew/etc/profile.d/autojump.sh /usr/local/etc/profile.d/autojump.sh "$HOME/.autojump/etc/profile.d/autojump.sh"; do
    [[ -r "$_df_jump" ]] && { source "$_df_jump"; break; }
  done
  unset _df_jump
fi

# Fast branch-only prompt: no worktree scan or Python process per prompt.
_dotfiles_precmd() {
  local code=$? branch='' context="${MY_ENV:-}" envname=''
  [[ ${DOTFILES_GIT_PROMPT:-1} == 1 ]] && branch=$(command git symbolic-ref --quiet --short HEAD 2>/dev/null)
  [[ -n ${VIRTUAL_ENV:-} ]] && envname=${VIRTUAL_ENV:t}
  [[ -z "$envname" && -n ${CONDA_DEFAULT_ENV:-} ]] && envname=$CONDA_DEFAULT_ENV
  context=${context//\%/%%}; envname=${envname//\%/%%}; branch=${branch//\%/%%}
  PROMPT=''
  (( code )) && PROMPT="%F{red}$code %f"
  [[ -n "$context" ]] && PROMPT+="%F{magenta}[$context]%f "
  [[ -n "$envname" ]] && PROMPT+="%F{green}($envname)%f "
  PROMPT+='%F{blue}%~%f'
  [[ -n "$branch" ]] && PROMPT+=" %F{yellow}$branch%f"
  PROMPT+=' %# '
  return 0
}
unsetopt PROMPT_SUBST
autoload -Uz add-zsh-hook
add-zsh-hook precmd _dotfiles_precmd
PROMPT='%F{blue}%~%f %# '

# Keep account/host-specific setup out of the repository.
if [[ ${DOTFILES_SKIP_LOCAL:-0} != 1 ]]; then
  [[ -r "$HOME/.zshrc_local" ]] && source "$HOME/.zshrc_local"
  [[ -r "$HOME/.config/personal/zshrc.local" ]] && source "$HOME/.config/personal/zshrc.local"
fi
# Private hooks may prepend tools; keep an already active environment authoritative.
if [[ -n ${VIRTUAL_ENV:-} && -d "$VIRTUAL_ENV/bin" ]]; then
  path=("$VIRTUAL_ENV/bin" $path)
elif [[ -n ${CONDA_PREFIX:-} && -d "$CONDA_PREFIX/bin" ]]; then
  path=("$CONDA_PREFIX/bin" $path)
fi
# This helper works both at a prompt and from scripts (ZLE is not always active).
set_my_env() {
  export MY_ENV=${1:-}
  _dotfiles_precmd
  [[ -n ${WIDGET:-} ]] && zle reset-prompt
  return 0
}
# Highlighting must load after all widgets, including local customizations.
if _dotfiles_plugin_file zsh-syntax-highlighting zsh-syntax-highlighting.zsh; then source "$REPLY"; fi
unset REPLY

dotfiles-doctor() {
  local label fn missing=0
  for label fn in completion compdef suggestions _zsh_autosuggest_start highlighting _zsh_highlight history-substring history-substring-search-up fzf-history fzf-history-widget directory-jump j; do
    if (( $+functions[$fn] )); then print -r -- "OK $label"; else
      if [[ $label == fzf-history && ( ! -o zle || ! -t 0 || ! -t 1 ) ]]; then print -r -- "SKIP $label (no terminal line editor)"
      else print -r -- "MISSING $label"; (( missing += 1 )); fi
    fi
  done
  print -r -- "Ctrl-R: $(bindkey -M viins '^R')"
  print -r -- "Up: $(bindkey -M viins '^[[A')"
  print -r -- "Python alias: ${aliases[python]:-none}"
  print -r -- 'Local overrides are retained; use DOTFILES_SKIP_LOCAL=1 to isolate them.'
  (( missing == 0 ))
}
