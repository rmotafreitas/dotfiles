#!/bin/sh
# Optional macOS preferences. Prints the commands by default; --apply runs them.
# Each line is a plain `defaults write`, so undo one with `defaults delete <domain> <key>`.
set -eu

if [ "$(uname -s)" != Darwin ]; then
    echo 'macOS only' >&2
    exit 1
fi

apply=0
[ "${1:-}" != --apply ] || apply=1

run() {
    if [ "$apply" = 1 ]; then
        "$@"
    else
        printf '%s\n' "$*"
    fi
}

run mkdir -p "$HOME/Pictures/Screenshots"

# Finder: show every file extension, a path bar and a status bar.
run defaults write NSGlobalDomain AppleShowAllExtensions -bool true
run defaults write com.apple.finder ShowPathbar -bool true
run defaults write com.apple.finder ShowStatusBar -bool true
# Do not litter network and USB volumes with .DS_Store files.
run defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
run defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true
# Save and print panels start expanded.
run defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
run defaults write NSGlobalDomain PMPrintingExpandedStateForPrint -bool true
# Faster key repeat (press-and-hold accents stay enabled for é, ã, ç).
run defaults write NSGlobalDomain KeyRepeat -int 2
run defaults write NSGlobalDomain InitialKeyRepeat -int 15
# Screenshots: PNG files in ~/Pictures/Screenshots without the window shadow.
run defaults write com.apple.screencapture location -string "$HOME/Pictures/Screenshots"
run defaults write com.apple.screencapture type -string png
run defaults write com.apple.screencapture disable-shadow -bool true

if [ "$apply" = 1 ]; then
    for app in Finder SystemUIServer; do
        killall "$app" >/dev/null 2>&1 || true
    done
    echo 'Applied. Log out and back in for the keyboard repeat settings.'
else
    echo 'Preview only. Add --apply to run these.' >&2
fi
