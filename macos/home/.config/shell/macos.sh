# macOS additions for Bash and Zsh. Installed only on Darwin and sourced by
# toolchain.sh before PATH is assembled. No network access; optional tools are
# used only when present.

# Homebrew (Apple Silicon, then Intel).
for _mac_brew in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [ -x "$_mac_brew" ]; then
        eval "$("$_mac_brew" shellenv)"
        break
    fi
done
unset _mac_brew

# pyenv: shims for every shell, shell integration is added by macos.zsh.
export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
for _mac_dir in "$PYENV_ROOT/bin" "$PYENV_ROOT/shims" "$HOME/.codeium/windsurf/bin" \
    "$HOME/claw-code/rust/target/debug" \
    "$HOME/Library/Application Support/JetBrains/Toolbox/scripts"; do
    [ ! -d "$_mac_dir" ] || PATH="$_mac_dir:$PATH"
done
unset _mac_dir

alias cw='claw --model opus'
alias cws='claw --model sonnet'
alias cwh='claw --model haiku'

# Interactive Bash: Homebrew completion and fzf key bindings.
if [ -n "${BASH_VERSION:-}" ]; then
    case $- in
    *i*)
        if [ -n "${HOMEBREW_PREFIX:-}" ] && [ -r "$HOMEBREW_PREFIX/etc/profile.d/bash_completion.sh" ]; then
            . "$HOMEBREW_PREFIX/etc/profile.d/bash_completion.sh"
        fi
        if command -v fzf >/dev/null 2>&1; then
            eval "$(fzf --bash 2>/dev/null)"
        fi
        ;;
    esac
fi
