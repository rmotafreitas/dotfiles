# TMF Keyboard for Linux (XKB)

US-International style layout with Portuguese/English accents. Converted from the Windows layout
`tmfkeyboard.klc`; the macOS version is `tmfkeyboard.keylayout`.

Files:
- `symbols/tmf` - the layout
- `rules/evdev.xml` - lets keyboard settings list it
- `install.sh` - user-level install (no root)

## Install (Wayland: GNOME, KDE Plasma, Sway, ...)

```sh
sh install.sh
```

Then log out and back in and add **TMF Keyboard** in Settings -> Keyboard. This uses
`~/.config/xkb`, which needs a recent libxkbcommon and does **not** work on an X11 session.
Check which you have with `echo $XDG_SESSION_TYPE`.

If it is not listed in Settings (some desktop versions ignore user `evdev.xml`):

- GNOME: `gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'tmf')]"`
- Sway: `input type:keyboard xkb_layout tmf`
- Hyprland: `kb_layout = tmf`

## Install (X11 session)

X11 servers cannot read `~/.config/xkb`. Compile on your side and send the result to the server:

```sh
mkdir -p ~/.config/xkb && cp -r symbols ~/.config/xkb/
setxkbmap -I$HOME/.config/xkb -layout tmf -print | xkbcomp -I$HOME/.config/xkb - $DISPLAY
```

That lasts until you log out; put the same line in `~/.xprofile` to make it permanent. System-wide
alternative (needs root): copy `symbols/tmf` to `/usr/share/X11/xkb/symbols/tmf`, then
`setxkbmap tmf`. Package updates do not remove a file they do not own.

## Typing

AltGr is the **Right Alt** key.

| You want | Type |
|---|---|
| a e i o u with acute (á é í ó ú) | AltGr + the vowel (add Shift for capitals) |
| ç Ç | AltGr + c, or AltGr + , |
| ã õ ñ | Shift+` (key left of 1), release, then a / o / n |
| â ê ô û î | Shift+6, release, then the vowel |
| à è ì ò ù | ` (key left of 1), release, then the vowel |
| ^ ~ ` on their own | the dead key, then Space |
| other | AltGr+5 = €, AltGr+q = ä, AltGr+w = å, AltGr+z = æ, AltGr+l = ø, AltGr+s = ß, AltGr+; = º, AltGr+/ = ¿, AltGr+[ = « |

`'` and `"` are normal keys (not dead). AltGr+`'` is a dead key that makes **grave** accents
(à è ì ò ù), same as the original Windows layout; use AltGr+vowel for acute.

## Differences from the Windows layout

- Dead keys use the system Compose tables, so they accept more letters than Windows did
  (e.g. `^` then `c` gives ĉ). Everything the original defined gives the same result.
- With Caps Lock on: AltGr+S gives ẞ and AltGr+M gives Μ (Windows keeps ß and µ), and
  Caps+Shift+AltGr+, gives Ç (Windows gives ç).
- The numpad decimal key keeps the system's NumLock behaviour.
- Ctrl combinations are the system's own.

## Remove

```sh
rm ~/.config/xkb/symbols/tmf
```
and, if `install.sh` created it, `~/.config/xkb/rules/evdev.xml`. Then remove the layout in Settings.

## Testing status

Compiled and checked on libxkbcommon 1.6 and 1.7 (`xkbcli compile-keymap`, and the classic X11
`xkbcomp`), with every key at every level, Caps Lock/AltGr behaviour, the special keys and all
dead-key sequences compared against the original `.klc`. **Not tested on a real desktop session.**
