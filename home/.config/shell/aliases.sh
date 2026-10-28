alias ll='ls -lah'
alias gs='git status'
alias gp='git pull'
alias gc='git commit'
alias dc='docker compose'
alias dps='docker ps'
alias tma='tmux attach -t'
alias tml='tmux ls'

# Debian and Ubuntu install bat and fd as batcat and fdfind.
if ! command -v bat >/dev/null 2>&1 && command -v batcat >/dev/null 2>&1; then
    alias bat='batcat'
fi
if ! command -v fd >/dev/null 2>&1 && command -v fdfind >/dev/null 2>&1; then
    alias fd='fdfind'
fi

# Stop whatever is listening on a TCP port: killport 3000 (killport 3000 -9 to force).
# Only listeners match, so browsers and other clients connected to the port are spared.
killport() {
    local pids
    pids=$(lsof -t -iTCP:"${1:?usage: killport PORT [-SIGNAL]}" -sTCP:LISTEN) || {
        echo "Nothing is listening on TCP port $1" >&2
        return 1
    }
    printf '%s\n' "$pids" | xargs kill "${2:--TERM}"
}
