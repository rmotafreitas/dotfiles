# Login Bash and noninteractive SSH commands share the same toolchain defaults.
if [ -n "${BASH_VERSION:-}" ]; then
    . "$HOME/.bashrc"
else
    [ ! -d "$HOME/.local/bin" ] || PATH="$HOME/.local/bin:$PATH"
    [ ! -d "$HOME/bin" ] || PATH="$HOME/bin:$PATH"
    export PATH
fi
