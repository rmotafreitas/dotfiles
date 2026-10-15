# macOS runs path_helper from /etc/zprofile after .zshenv, moving system
# directories ahead of the toolchain (so /usr/bin/java beats SDKMAN). Put the
# PATH that toolchain.sh built back in front; duplicates keep their first place.
if [[ -n ${_DOTFILES_PATH-} ]]; then
    typeset -U path PATH
    PATH="$_DOTFILES_PATH:$PATH"
fi
