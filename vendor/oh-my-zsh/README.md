# Oh My Zsh Git lib / plugin

These two unmodified files provide the full public Git aliases and helpers without
starting the Oh My Zsh framework or a plugin updater. They come from the official
[Oh My Zsh repository](https://github.com/ohmyzsh/ohmyzsh) at commit
`4d4cfc287e9d887b81242c0e431b5f49f9cec5c1`. The MIT license is included;
`source.json` records each source path and SHA256.

`shell/git.zsh` loads them after compinit, once per shell. Framework-dependent async
prompt support is disabled; the public prompt uses one read-only Git status call.
Private aliases can override the defaults after loading. Destructive helpers are
available for explicit invocation and are never run during startup.

Before updating, review the upstream diff, preserve the license, refresh the
manifest hashes, and rerun shell tests. Startup does not fetch or update these files.

The upstream plugin contains blank lines with trailing spaces. A scoped Git
whitespace attribute preserves those bytes; authored files retain normal checks.
