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
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init bash)"
else
    PS1='\u@\h:\w\$ '
fi
[ ! -r "$HOME/.bashrc.local" ] || . "$HOME/.bashrc.local"
