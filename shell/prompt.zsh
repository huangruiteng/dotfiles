# One read-only Git status call per prompt; no Python or async runtime.
_dotfiles_precmd() {
  local code=$? context="${MY_ENV-personal}" envname='' git_out='' git_head='' git_oid=''
  local git_ahead=0 git_behind=0 git_staged=0 git_unstaged=0 git_untracked=0 git_conflicts=0
  local line xy git_label='' summary='' style=${DOTFILES_PROMPT_STYLE:-powerline}
  local -a fields
  [[ -n ${VIRTUAL_ENV:-} ]] && envname=${VIRTUAL_ENV:t}
  [[ -z $envname && -n ${CONDA_DEFAULT_ENV:-} ]] && envname=$CONDA_DEFAULT_ENV
  context=${context//\%/%%}; envname=${envname//\%/%%}
  if [[ ${DOTFILES_GIT_PROMPT:-1} == 1 ]]; then
    git_out=$(command git --no-optional-locks status --porcelain=v2 --branch 2>/dev/null)
    for line in "${(@f)git_out}"; do
      case "$line" in
        '# branch.head '*) git_head=${line#\# branch.head } ;;
        '# branch.oid '*) git_oid=${line#\# branch.oid } ;;
        '# branch.ab '*) fields=(${=line}); git_ahead=${fields[3]#+}; git_behind=${fields[4]#-} ;;
        '1 '*|'2 '*)
          fields=(${=line}); xy=$fields[2]
          [[ ${xy[1]} != '.' ]] && (( git_staged++ ))
          [[ ${xy[2]} != '.' ]] && (( git_unstaged++ )) ;;
        'u '*) (( git_conflicts++ )) ;;
        '? '*) (( git_untracked++ )) ;;
      esac
    done
    if [[ -n $git_head ]]; then
      [[ $git_head == '(detached)' ]] && git_head="@${git_oid[1,8]}"
      git_head=${git_head//\%/%%}
      (( git_ahead )) && summary+=" ↑${git_ahead}"
      (( git_behind )) && summary+=" ↓${git_behind}"
      (( git_staged )) && summary+=" %F{70}+${git_staged}"
      (( git_unstaged )) && summary+=" %F{203}✚${git_unstaged}"
      (( git_untracked )) && summary+=" %F{240}…${git_untracked}"
      (( git_conflicts )) && summary+=" %F{magenta}✖${git_conflicts}"
      (( git_staged + git_unstaged + git_untracked + git_conflicts == 0 )) && summary+=' %F{112}✔'
    fi
  fi
  if [[ $style == compact ]]; then
    PROMPT=''
    (( code )) && PROMPT="%F{red}$code %f"
    [[ -n $context ]] && PROMPT+="%F{magenta}[$context]%f "
    [[ -n $envname ]] && PROMPT+="%F{green}($envname)%f "
    PROMPT+='%F{blue}%~%f'
    [[ -n $git_head ]] && PROMPT+=" %F{yellow}${git_head}${summary}%f"
    PROMPT+=' %# '
    return 0
  fi
  PROMPT='%K{236}'
  (( code )) && PROMPT+='%F{203} ● ' || PROMPT+='%F{112} ● '
  [[ -n $context ]] && PROMPT+="%K{33}%F{236}%F{white} 📌 ${context} %K{236}%F{33}"
  [[ -n $envname ]] && PROMPT+="%K{35}%F{236}%F{white} (${envname}) %K{236}%F{35}"
  PROMPT+='%F{245} %D{%H:%M:%S} %K{153}%F{236}%F{240} %3~ '
  if [[ -n $git_head ]]; then
    PROMPT+="%K{230}%F{153}%F{240}  ${git_head} %F{240}${summary} %k%F{230}%f "
  else PROMPT+='%k%F{153}%f '; fi
  return 0
}

# Applies only to a real local iTerm session with the managed profile installed.
dotfiles-iterm-refresh() {
  [[ ${DOTFILES_ITERM_APPEARANCE:-1} == 1 && ${TERM_PROGRAM:-} == iTerm.app && -t 1 && -z ${TMUX:-} ]] || return 0
  [[ -r "$HOME/Library/Application Support/iTerm2/DynamicProfiles/dotfiles-personal.json" ]] || return 0
  printf '\e]1337;SetProfile=Dotfiles Meslo Pastel\a'
  # Running sessions cache fonts; SetProfile alone can leave the old Monaco font.
  printf '\e]1337;SetProfileProperty=Normal Font=Ik1lc2xvTEdTTkZNLVJlZ3VsYXIgMTQi;Non Ascii Font=Ik1lc2xvTEdTTkZNLVJlZ3VsYXIgMTQi;Use Non-ASCII Font=dHJ1ZQ==\a'
}
