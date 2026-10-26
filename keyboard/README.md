# TMF Keyboard

My US-International keyboard layout with Portuguese accents, where `'` and `"` are normal keys instead of dead keys. AltGr (Right Alt, Option on a Mac) + vowel gives á é í ó ú, AltGr + c gives ç, and `~`, `^` and `` ` `` are dead keys for ã õ, â ê ô and à. The full key table is in [linux/README.md](linux/README.md#typing).

| OS | File |
| --- | --- |
| Windows | [windows/tmfkeyboard.klc](windows/tmfkeyboard.klc), the original source |
| macOS | [macos/tmfkeyboard.keylayout](macos/tmfkeyboard.keylayout) |
| Linux | [linux/](linux/), XKB layout with `install.sh` |

The macOS and Linux files are generated from the `.klc` by the scripts in [tools/](tools/).

## Windows

The `.klc` must be built into an installer with Microsoft Keyboard Layout Creator (MSKLC). Installing the result needs administrator rights.

1. Download **Microsoft Keyboard Layout Creator 1.4** from Microsoft's download center and install it. If it asks for .NET Framework 3.5, enable it in **Turn Windows features on or off**.
2. Download [tmfkeyboard.klc](windows/tmfkeyboard.klc): open it on GitHub and click **Download raw file**. Do not copy and paste the text; the file must stay UTF-16.
3. In MSKLC: **File → Load Source File…**, select `tmfkeyboard.klc`, then **Project → Build DLL and Setup Package**. It writes a `tmfusint` folder (in Documents by default).
4. Run `setup.exe` from that folder, then sign out and back in.
5. **Settings → Time & language → Language & region**: the layout is registered for **Portuguese (Portugal)**. Under that language's **Language options**, add the keyboard **US-Intern.No dead PT-US** (add the language first if it is missing). Switch layouts with Win + Space.

To remove it, uninstall **US-Intern.No dead PT-US** from **Installed apps**.

Without admin rights, add Windows' built-in **United States-International** keyboard instead. It types the same AltGr accents, but `'` and `"` are dead keys: press Space after them to get the plain character.

## macOS

```sh
cp keyboard/macos/tmfkeyboard.keylayout ~/Library/Keyboard\ Layouts/
```

Log out and back in, then add **TMF Keyboard** under **System Settings → Keyboard → Text Input → Edit… → +** (listed under **Others**).

## Linux

```sh
sh keyboard/linux/install.sh
```

Then log out and add **TMF Keyboard** in keyboard settings. See [linux/README.md](linux/README.md) for X11 sessions and removal.

## Rebuilding

After editing the `.klc` (for example in MSKLC):

```sh
python3 -I keyboard/tools/klc2keylayout.py keyboard/windows/tmfkeyboard.klc keyboard/macos/tmfkeyboard.keylayout "TMF Keyboard"
python3 -I keyboard/tools/klc2xkb.py keyboard/windows/tmfkeyboard.klc keyboard/linux
```

`tools/test_xkb.py` checks the Linux layout against the `.klc` through the real libxkbcommon (Linux only).
