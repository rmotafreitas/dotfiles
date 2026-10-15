# Shared Bash/Zsh toolchain setup. No version numbers and no network access.
# This guard is intentionally not exported: each new shell initializes itself.
if [ "${_USER_TOOLCHAIN_READY:-}" = 1 ]; then
    return 0
fi
_USER_TOOLCHAIN_READY=1

# Private machine overrides are loaded before automatic discovery.
[ ! -r "$HOME/.config/shell/local.sh" ] || . "$HOME/.config/shell/local.sh"
# Platform additions (for example Homebrew on macOS) exist only where installed.
[ ! -r "$HOME/.config/shell/macos.sh" ] || . "$HOME/.config/shell/macos.sh"

# Respect custom manager locations; otherwise discover the existing installation.
if [ -z "${NVM_DIR:-}" ]; then
    if [ -s "$HOME/.config/nvm/nvm.sh" ]; then
        NVM_DIR="$HOME/.config/nvm"
    else
        NVM_DIR="$HOME/.nvm"
    fi
fi
export NVM_DIR
export SDKMAN_DIR="${SDKMAN_DIR:-$HOME/.sdkman}"
export BUN_INSTALL="${BUN_INSTALL:-$HOME/.bun}"
export CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}"
export RUSTUP_HOME="${RUSTUP_HOME:-$HOME/.rustup}"

# NVM owns Node/npm/npx selection. Preserve an explicitly selected parent runtime.
# Homebrew installs nvm.sh outside NVM_DIR, which still holds the Node versions.
_tc_nvm=$NVM_DIR/nvm.sh
if [ ! -s "$_tc_nvm" ] && [ -n "${HOMEBREW_PREFIX:-}" ]; then
    _tc_nvm=$HOMEBREW_PREFIX/opt/nvm/nvm.sh
fi
if [ -s "$_tc_nvm" ]; then
    if [ -n "${NVM_BIN:-}" ] && [ -x "$NVM_BIN/node" ] &&
       [ "$(command -v node)" = "$NVM_BIN/node" ]; then
        . "$_tc_nvm" --no-use
    else
        . "$_tc_nvm"
    fi
fi

# SDKMAN supplies current defaults. Preserve explicit toolchain overrides from CI.
_tc_java=${JAVA_HOME:-}
_tc_gradle=${GRADLE_HOME:-}
_tc_maven=${MAVEN_HOME:-}
_tc_ant=${ANT_HOME:-}
if [ -s "$SDKMAN_DIR/bin/sdkman-init.sh" ]; then
    . "$SDKMAN_DIR/bin/sdkman-init.sh"
fi
[ -z "$_tc_java" ] || export JAVA_HOME="$_tc_java"
[ -z "$_tc_gradle" ] || export GRADLE_HOME="$_tc_gradle"
[ -z "$_tc_maven" ] || export MAVEN_HOME="$_tc_maven"
[ -z "$_tc_ant" ] || export ANT_HOME="$_tc_ant"

# ANDROID_HOME is authoritative. Keep the legacy alias consistent for older tools.
if [ -z "${ANDROID_HOME:-}" ]; then
    if [ -n "${ANDROID_SDK_ROOT:-}" ]; then
        ANDROID_HOME=$ANDROID_SDK_ROOT
    else
        for _tc_sdk in "$HOME/Android/Sdk" "$HOME/Library/Android/sdk" /usr/lib/android-sdk /opt/android-sdk; do
            if [ -d "$_tc_sdk/platform-tools" ]; then
                ANDROID_HOME=$_tc_sdk
                break
            fi
        done
    fi
fi
if [ -n "${ANDROID_HOME:-}" ]; then
    export ANDROID_HOME
    export ANDROID_SDK_ROOT="$ANDROID_HOME"
fi

# Add only existing directories, with explicit SDK selections ahead of defaults.
for _tc_dir in "${ANT_HOME:+$ANT_HOME/bin}" "${MAVEN_HOME:+$MAVEN_HOME/bin}" \
    "${GRADLE_HOME:+$GRADLE_HOME/bin}" "${JAVA_HOME:+$JAVA_HOME/bin}" \
    "$CARGO_HOME/bin" "$BUN_INSTALL/bin" "$HOME/.opencode/bin" \
    "${ANDROID_HOME:+$ANDROID_HOME/emulator}" \
    "${ANDROID_HOME:+$ANDROID_HOME/cmdline-tools/latest/bin}" \
    "${ANDROID_HOME:+$ANDROID_HOME/platform-tools}" "$HOME/.local/bin" "$HOME/bin"; do
    [ -d "$_tc_dir" ] && PATH="$_tc_dir:$PATH"
done
# Deduplicate without external commands; preserve first-entry precedence.
_tc_rest=$PATH
_tc_path=
_tc_first=1
while :; do
    _tc_item=${_tc_rest%%:*}
    case ":$_tc_path:" in
        *:"$_tc_item":*) ;;
        *) if [ "$_tc_first" = 1 ]; then
               _tc_path=$_tc_item
               _tc_first=0
           else
               _tc_path="$_tc_path:$_tc_item"
           fi ;;
    esac
    case $_tc_rest in *:*) _tc_rest=${_tc_rest#*:} ;; *) break ;; esac
done
export PATH=$_tc_path
# Remembered so a login shell can restore precedence after the system's PATH rewrite (see .zprofile).
_DOTFILES_PATH=$_tc_path
unset _tc_nvm _tc_java _tc_gradle _tc_maven _tc_ant _tc_sdk _tc_dir _tc_rest _tc_path _tc_first _tc_item
