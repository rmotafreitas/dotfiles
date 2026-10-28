# SSH invokes this before the interactive guard on supported Bash setups.
. "$HOME/.config/shell/toolchain.sh"
case $- in *i*) ;; *) return ;; esac
export EDITOR="${EDITOR:-vim}"
export VISUAL="${VISUAL:-$EDITOR}"
HISTCONTROL=ignoreboth
HISTSIZE=50000
HISTFILESIZE=50000
shopt -s histappend checkwinsize
. "$HOME/.config/shell/aliases.sh"
if [ -r /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
fi
# Colors for ls and grep (BSD/macOS ls reads CLICOLOR, GNU ls needs --color); NO_COLOR turns them off.
if [ -z "${NO_COLOR:-}" ]; then
    export CLICOLOR=1
    if ls --color=auto -d . >/dev/null 2>&1; then
        alias ls='ls --color=auto'
    else
        alias ls='ls -G'
    fi
    alias grep='grep --color=auto'
fi
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init bash)"
elif [ -z "${NO_COLOR:-}" ]; then
    PS1='\[\e[32m\]\u@\h\[\e[0m\]:\[\e[34m\]\w\[\e[0m\]\$ '
else
    PS1='\u@\h:\w\$ '
fi
# T3 Chat terminal colors (light unless `t3-theme dark`).
[ ! -r "$HOME/.config/shell/t3-chat.sh" ] || . "$HOME/.config/shell/t3-chat.sh"
[ ! -r "$HOME/.bashrc.local" ] || . "$HOME/.bashrc.local"
