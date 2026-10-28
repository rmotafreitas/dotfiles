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

# fzf matches and pointer in T3 Chat pink; the rest follows the terminal's colors.
export FZF_DEFAULT_OPTS="${FZF_DEFAULT_OPTS-"--color=hl:#db2777,hl+:#db2777,pointer:#db2777,marker:#db2777,prompt:#db2777,spinner:#db2777"}"
# bat highlights with the terminal's 16 colors, so it stays readable in both T3 Chat modes.
export BAT_THEME="${BAT_THEME-ansi}"
