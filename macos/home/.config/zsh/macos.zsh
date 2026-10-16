# macOS interactive extras, sourced near the end of .zshrc.
[[ ! -r $HOME/.p10k.zsh ]] || source "$HOME/.p10k.zsh"

# fzf key bindings and completion, unless the Oh My Zsh fzf plugin already set them up.
if (( $+commands[fzf] && ! $+functions[fzf-history-widget] )); then
    source <(fzf --zsh)
fi

# pyenv shell integration; the shims are already on PATH from macos.sh.
if (( $+commands[pyenv] )); then
    eval "$(pyenv init -)"
    (( ! $+commands[pyenv-virtualenv-init] )) || eval "$(pyenv virtualenv-init -)"
fi

# nvm completion from Homebrew's nvm.
[[ -z ${HOMEBREW_PREFIX-} || ! -s $HOMEBREW_PREFIX/opt/nvm/etc/bash_completion.d/nvm ]] ||
    source "$HOMEBREW_PREFIX/opt/nvm/etc/bash_completion.d/nvm"

# Show system info once, before the first prompt. Powerlevel10k's instant prompt still has
# stdout redirected here, so fastfetch would see a pipe and drop its colors: keep them.
_fastfetch_once() {
    (( $+commands[fastfetch] )) && fastfetch --pipe false
    precmd_functions=(${precmd_functions:#_fastfetch_once})
}
precmd_functions+=(_fastfetch_once)

# bag: list what blocks sleep, then offer to sleep anyway.
bag() {
    echo "🔍 A verificar o que está a bloquear o sleep...\n"
    local blockers=$(pmset -g assertions | grep -E "^\s+pid" | grep "PreventUserIdle\|PreventSystem")
    if [[ -z "$blockers" ]]; then
        echo "✅ Nada a bloquear o sleep."
    else
        echo "⚠️  Estas cenas estão a bloquear:\n"
        echo "$blockers" | while read line; do
            echo "  $line"
        done
    fi
    echo ""
    read "resposta?👜 Ir para sleep mesmo assim? [s/N] "
    if [[ "$resposta" =~ ^[sSyY]$ ]]; then
        echo "😴 Sleeping..."
        pmset sleepnow
    else
        echo "❌ Cancelado."
    fi
}
