# macOS prelude, sourced first by .zshrc. The Powerlevel10k instant prompt must
# run before anything prints, so it lives here rather than in macos.zsh.
_p10k_theme="${ZSH_CUSTOM:-${ZSH:-$HOME/.oh-my-zsh}/custom}/themes/powerlevel10k/powerlevel10k.zsh-theme"
if [[ -r $_p10k_theme ]]; then
    DOTFILES_ZSH_THEME=powerlevel10k/powerlevel10k
    typeset -g POWERLEVEL9K_INSTANT_PROMPT=quiet
    if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
        source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
    fi
fi
unset _p10k_theme

# Docker Desktop ships completions that must be on fpath before compinit.
fpath=(/Applications/Docker.app/Contents/Resources/etc(N-/) $fpath)

# Extra Oh My Zsh plugins; names that are not installed are skipped.
dotfiles_plugins=()
for _plugin in docker-compose macos sdk fzf; do
    [[ ! -d "${ZSH:-$HOME/.oh-my-zsh}/plugins/$_plugin" ]] || dotfiles_plugins+=($_plugin)
done
(( ! $+commands[autojump] )) || [[ ! -d "${ZSH:-$HOME/.oh-my-zsh}/plugins/autojump" ]] || dotfiles_plugins+=(autojump)
unset _plugin
