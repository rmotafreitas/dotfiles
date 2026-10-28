# Platform prelude (macOS: Powerlevel10k instant prompt); must stay first.
[[ ! -r "$HOME/.config/zsh/macos-pre.zsh" ]] || source "$HOME/.config/zsh/macos-pre.zsh"
typeset -U path PATH
export ZSH="${ZSH:-$HOME/.oh-my-zsh}"
ZSH_THEME="${DOTFILES_ZSH_THEME:-}"
plugins=(git docker npm $dotfiles_plugins)
(( ! $+commands[tmux] )) || plugins+=(tmux)
for plugin in zsh-autosuggestions zsh-syntax-highlighting; do
    [[ ! -r "${ZSH_CUSTOM:-$ZSH/custom}/plugins/$plugin/$plugin.plugin.zsh" ]] || plugins+=($plugin)
done
unset plugin
if [[ -r "$ZSH/oh-my-zsh.sh" ]]; then
    source "$ZSH/oh-my-zsh.sh"
else
    autoload -Uz compinit
    compinit
fi
export EDITOR="${EDITOR:-vim}"
export VISUAL="${VISUAL:-$EDITOR}"
HISTFILE="$HOME/.zsh_history"
HISTSIZE=50000
SAVEHIST=50000
setopt HIST_IGNORE_DUPS HIST_IGNORE_SPACE SHARE_HISTORY APPEND_HISTORY
source "$HOME/.config/shell/aliases.sh"
alias reload='exec zsh'
if [[ -n "${DOTFILES_ZSH_THEME-}" ]]; then
    : # the Oh My Zsh theme provides the prompt
elif command -v starship >/dev/null 2>&1; then
    eval "$(starship init zsh)"
else
    PROMPT='%n@%m:%~%# '
fi
for completion in /usr/share/doc/fzf/examples/key-bindings.zsh /usr/share/doc/fzf/examples/completion.zsh "$NVM_DIR/bash_completion" "$BUN_INSTALL/_bun"; do
    [[ ! -r "$completion" ]] || source "$completion"
done
unset completion
# Reuse the login-session agent; do not spawn agents or prompt for keys at startup.
if [[ -z "$SSH_AUTH_SOCK" && -S "/run/user/$UID/openssh_agent" ]]; then
    SSH_AUTH_SOCK="/run/user/$UID/openssh_agent" ssh-add -l >/dev/null 2>&1
    (( $? > 1 )) || export SSH_AUTH_SOCK="/run/user/$UID/openssh_agent"
fi
# T3 Chat terminal colors and highlighting (light unless `t3-theme dark`); before fastfetch, so it shows in them.
[[ ! -r "$HOME/.config/shell/t3-chat.sh" ]] || source "$HOME/.config/shell/t3-chat.sh"
# Show system info once, before the first prompt. Powerlevel10k's instant prompt still has
# stdout redirected here, so fastfetch would see a pipe and drop its colors: keep them.
_fastfetch_once() {
    (( $+commands[fastfetch] )) && fastfetch --pipe false
    precmd_functions=(${precmd_functions:#_fastfetch_once})
}
precmd_functions+=(_fastfetch_once)
[[ ! -r "$HOME/.config/zsh/macos.zsh" ]] || source "$HOME/.config/zsh/macos.zsh"
[[ ! -r "$HOME/.zshrc.local" ]] || source "$HOME/.zshrc.local"
