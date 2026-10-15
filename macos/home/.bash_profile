# macOS starts Bash as a login shell, which reads this file instead of .profile.
[ ! -r "$HOME/.profile" ] || . "$HOME/.profile"
