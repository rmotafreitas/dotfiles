#!/bin/sh
# Install the "TMF Keyboard" XKB layout for the current user (Wayland / anything using libxkbcommon).
# Nothing outside ~/.config/xkb is touched, and an existing rules/evdev.xml is never overwritten.
set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
dest="${XDG_CONFIG_HOME:-$HOME/.config}/xkb"

# An erroneous layout can make a keyboard unusable, so compile it first if we can.
if command -v xkbcli >/dev/null 2>&1; then
  if xkbcli compile-keymap --include "$here" --include-defaults \
       --rules evdev --model pc105 --layout tmf >/dev/null 2>&1; then
    echo "compile check: ok"
  else
    echo "compile check FAILED - not installing anything" >&2
    exit 1
  fi
else
  echo "note: 'xkbcli' not found, skipping the compile check (package: libxkbcommon-tools)"
fi

mkdir -p "$dest/symbols" "$dest/rules"
cp "$here/symbols/tmf" "$dest/symbols/tmf"
echo "installed: $dest/symbols/tmf"

if [ ! -e "$dest/rules/evdev.xml" ]; then
  cp "$here/rules/evdev.xml" "$dest/rules/evdev.xml"
  echo "installed: $dest/rules/evdev.xml (lets Settings list the layout)"
elif grep -q '<name>tmf</name>' "$dest/rules/evdev.xml"; then
  echo "evdev.xml already lists tmf - left as is"
else
  echo "NOT changing your existing $dest/rules/evdev.xml."
  echo "To make Settings list the layout, add the <layout> block from"
  echo "  $here/rules/evdev.xml"
  echo "inside the <layoutList> of that file. (The layout still works without it, see README.)"
fi

echo
echo "Done. Log out and back in, then add 'TMF Keyboard' in your keyboard settings."
echo "If it is not listed:  gsettings set org.gnome.desktop.input-sources sources \"[('xkb', 'tmf')]\""
