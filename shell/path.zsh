# No subprocesses or package-manager initialization in the startup path.
typeset -U path PATH
for _df_dir in "$HOME/.local/bin" "$HOME/.cargo/bin" "$HOME/.npm-global/bin" "$HOME/.mybin" /opt/homebrew/bin /opt/homebrew/sbin /usr/local/bin /usr/local/sbin; do
  [[ -d "$_df_dir" ]] && path+=("$_df_dir")
done
# Preserve activated virtualenvs and version managers ahead of fallback tools.
if (( ! $+commands[node] )); then
  for _df_dir in /opt/homebrew/opt/node@24/bin /usr/local/opt/node@24/bin; do
    [[ -d "$_df_dir" ]] && path+=("$_df_dir")
  done
fi
export PATH
unset _df_dir

# Keep user-installed manuals without hiding the system's default search path.
if [[ -d "$HOME/.local/share/man" && ":${MANPATH:-}:" != *":$HOME/.local/share/man:"* ]]; then
  export MANPATH="$HOME/.local/share/man:${MANPATH:-}"
fi

# The Homebrew runtime and shell integration must agree. Retire only the old
# standalone fzf bin path when a maintained Homebrew binary is available.
if [[ -x /opt/homebrew/bin/fzf || -x /usr/local/bin/fzf ]]; then
  path=("${(@)path:#${HOME}/.fzf/bin}")
elif (( ! $+commands[fzf] )) && [[ -d "$HOME/.fzf/bin" ]]; then
  path+=("$HOME/.fzf/bin")
fi
