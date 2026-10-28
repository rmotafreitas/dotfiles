# Ricardo's dotfiles

My Bash, Zsh, Git and tmux setup, with shared automatic toolchain discovery for Android development and CI. Linux first, tested on Debian and in isolated temporary home directories. A macOS layer (Homebrew, Powerlevel10k, Ghostty) is installed only on macOS and checked in CI on a macOS runner.

The shell config follows installed NVM/SDKMAN defaults instead of hard-coding version paths. Explicit environment overrides still win, so a CI job can pin Java while interactive shells use another default.

## Install

Requires Git and Python 3.9+. Bash and Zsh are needed for the full test suite.

```sh
git clone https://github.com/rmotafreitas/dotfiles.git ~/dotfiles
cd ~/dotfiles
python3 scripts/install.py          # preview; changes nothing
python3 scripts/install.py --apply  # back up conflicts, then create symlinks
```

Open a new terminal afterward. The installer manages the configuration files listed in `scripts/install.py` (eight everywhere, plus the macOS files on a Mac; `--platform linux|darwin` overrides detection); `--wallpapers` also installs the four wallpaper images. Re-running it is safe. Existing files and symlinks are moved into `~/.local/state/dotfiles/backups/<timestamp>/`. Keep this checkout where it is: the installed files link to it.

An existing `~/.gitconfig` is also copied to `~/.gitconfig.local` if that private file does not exist, preserving identity and credential helpers. On a new machine, set these locally:

```sh
git config --file ~/.gitconfig.local user.name 'Your Name'
git config --file ~/.gitconfig.local user.email 'your-github-noreply-address'
```

The installer does not install packages, fetch plugins, change your login shell, modify CI projects, or restart services. If you already use `.bash_profile`/`.bash_login` or a custom `ZDOTDIR`, integrate the supplied files into that setup explicitly.

## What's included

| File | Purpose |
| --- | --- |
| `.config/shell/toolchain.sh` | Shared toolchain discovery and PATH deduplication |
| `.config/shell/aliases.sh` | Git, Docker and tmux shortcuts, `bat`/`fd` names on Debian, `killport` |
| `.zshenv` | Toolchain environment for Zsh, including SSH commands |
| `.zshrc` | History, optional plugins, prompt, completions, agent reuse and fastfetch on the first prompt |
| `.bashrc` / `.profile` | Interactive Bash and login/SSH initialization |
| `.gitconfig` | Defaults (`main` branch, fast-forward pulls, auto upstream on push, zdiff3 conflicts), then private identity and credentials |
| `.tmux.conf` | Ctrl-a prefix, mouse, splits, scrollback and optional TPM plugins |
| `linux/` | Debian package lists and their installer, described below |
| `macos/` | Optional macOS layer, described below |

### Automatic environment

- **Node/npm/npx:** NVM's default, or a valid runtime inherited from the parent shell. Supports NVM in `~/.config/nvm` or `~/.nvm`.
- **Java, Gradle, Maven, Ant:** SDKMAN's selected `current` versions. Explicit `*_HOME` overrides are preserved and their executable paths take precedence.
- **Android:** explicit `ANDROID_HOME`, then `ANDROID_SDK_ROOT`, then common SDK locations. The legacy variable mirrors `ANDROID_HOME` for compatibility.
- **Bun/Rust:** their installation homes; directories are added only when present.
- **PATH:** repeated entries are removed, retaining the first occurrence.

“Automatic” means selecting installed tools. Startup never downloads or upgrades them and does not switch versions on every directory change. Use `nvm use` / `nvm alias default` and `sdk use` / `sdk default` to select versions. Plain noninteractive `bash -c` inherits its environment; it does not ordinarily read `.bashrc`.

### Optional tools

The setup works without these. Install only what you use through their official instructions:

- [Oh My Zsh](https://ohmyz.sh/) and optionally `zsh-autosuggestions` / `zsh-syntax-highlighting` in its custom plugins directory.
- [Starship](https://starship.rs/) for the prompt; a basic prompt is used otherwise.
- [NVM](https://github.com/nvm-sh/nvm), [SDKMAN](https://sdkman.io/), [Bun](https://bun.sh/), [Rustup](https://rustup.rs/), and the [Android SDK](https://developer.android.com/tools).
- [fzf](https://github.com/junegunn/fzf) for completion/key bindings on Debian-style installations.
- [TPM](https://github.com/tmux-plugins/tpm) at `~/.tmux/plugins/tpm` for the configured tmux plugins. Use prefix + I after installing TPM.

Zsh reuses an existing SSH session agent when available. It does not spawn extra agents or load private keys at startup.

## Linux packages

[linux/packages/debian.txt](linux/packages/debian.txt) lists the packages I install from the Debian archive (fastfetch, btop, htop, bat, fzf, tmux, ffmpeg, diagnostics tools and so on), and [third-party.txt](linux/packages/third-party.txt) lists the ones from vendor repositories (Docker, GitHub CLI, Tailscale, Brave), with a link to each vendor's setup instructions. The base system and the XFCE desktop come from the Debian installer and are not listed.

```sh
sh linux/packages.sh          # show what is missing; changes nothing
sh linux/packages.sh --apply  # sudo apt-get install the missing packages
```

Only missing packages are installed and nothing is removed. Packages that no configured apt source provides, such as a vendor package before its repository is added, are reported and skipped.

These come from their own installers instead of apt, usually because Debian's version is older:

| Tool | Source |
| --- | --- |
| Rust | [rustup](https://rustup.rs/) |
| Node, `@openai/codex`, `eas-cli` | [NVM](https://github.com/nvm-sh/nvm), then `npm install -g` |
| Java, Gradle, Maven, Ant | [SDKMAN](https://sdkman.io/) |
| Bun | [bun.sh](https://bun.sh/) |
| Claude Code | [native installer](https://code.claude.com/docs/en/setup) |
| Starship, dust | Release binaries in `/usr/local/bin` (`starship` and `du-dust` are also in Debian) |
| lazydocker, jq, yt-dlp, ccache | Release binaries in `~/.local/bin` |
| Oh My Zsh, zsh-autosuggestions, zsh-syntax-highlighting, TPM | Git clones, see [Optional tools](#optional-tools) |

## macOS

On macOS the installer also links the files in [macos/](macos/), and Linux machines never see them:

| File | Purpose |
| --- | --- |
| `.config/shell/macos.sh` | Homebrew, pyenv and extra `PATH` entries; Bash completion and fzf for interactive Bash |
| `.config/zsh/macos-pre.zsh` | Powerlevel10k instant prompt, Docker completions and the extra Oh My Zsh plugins; skipped when not installed |
| `.config/zsh/macos.zsh` | p10k config, fzf, pyenv integration and the `bag` helper |
| `.zprofile` | Restores the toolchain `PATH` after macOS's `path_helper` has moved system directories to the front |
| `.bash_profile` | macOS login shells read this instead of `.profile` |
| `.p10k.zsh` | Powerlevel10k prompt configuration |
| Ghostty `config.ghostty` | Linked to `~/Library/Application Support/com.mitchellh.ghostty/` |

With Oh My Zsh and Powerlevel10k installed the prompt comes from p10k, otherwise from Starship or the basic prompt. Install the packages with `brew bundle --file=macos/Brewfile` (it includes the MesloLGS Nerd Font that the prompt and Ghostty use). `sh macos/defaults.sh` previews a few Finder, keyboard and screenshot preferences and `--apply` sets them; each can be undone with `defaults delete`.

Keep secrets such as API keys in `~/.zshrc.local` or `~/.config/shell/local.sh`, not in the repository. Put `[credential] helper = osxkeychain` in `~/.gitconfig.local`.

## Wallpapers

The [wallpapers/](wallpapers/) folder preserves my four original wallpaper files, including the images used by my XFCE desktop and Mac. Images are stored directly in Git (about 90 MiB total), so a normal clone includes them.

```sh
python3 scripts/install.py --wallpapers          # preview config + wallpaper links
python3 scripts/install.py --apply --wallpapers  # link into ~/Pictures/Wallpapers
```

Existing pictures are preserved. In XFCE, open **Desktop Settings → Background**, choose `~/Pictures/Wallpapers`, then select an image for each monitor/workspace. The installer does not change the current wallpaper or import monitor-specific XFCE settings. See the [gallery and asset notes](wallpapers/README.md).

## VS Code

[vscode/](vscode/) holds my VS Code settings, snippets and extension list, plus `ricardo.code-profile` built from them. Import it without signing in: **Command Palette → Profiles: Import Profile…**, paste

```text
https://raw.githubusercontent.com/rmotafreitas/dotfiles/main/vscode/ricardo.code-profile
```

then choose what to include and create the profile. After editing files in `vscode/`, run `python3 scripts/vscode_profile.py` to rebuild the profile. Machine-specific paths (Snyk, Maven, JavaFX, YAML schemas, SSH hosts) are left out.

## Keyboard layout

[keyboard/](keyboard/) has my TMF Keyboard layout (US-International with Portuguese accents) for Windows, macOS and Linux, with install steps for each.

## Private and machine-specific settings

These files live **outside this repository**:

- `~/.config/shell/local.sh` — environment overrides loaded before toolchain discovery; use Bash/Zsh-compatible syntax.
- `~/.bashrc.local` and `~/.zshrc.local` — interactive customizations loaded last.
- `~/.gitconfig.local` — Git identity and credential helpers.

Example `~/.config/shell/local.sh`:

```sh
export ANDROID_HOME="$HOME/Android/Sdk"
# Optionally select a different manager directory or pin a toolchain here.
```

Never commit keys, tokens, credential stores, history, app state or local override files. The repository contains a curated allowlist of configuration, not a copy of the home directory.

## Update, validate and undo

```sh
cd ~/dotfiles
git pull --ff-only
python3 scripts/install.py
python3 -m unittest discover -s tests -v
```

Symlinked files reflect edits immediately; shell initialization changes take effect in a new shell. Review updates before reloading. To restore an old file, remove only its installed symlink and move the matching file from the printed backup directory back to its original location. Local overrides are not removed by the installer.

GitHub Actions checks shell syntax and tests preview behavior, backups, repeat installation, destination boundaries and shell startup without optional tools.

## References

The layout uses the symlink approach seen in [Holman's dotfiles](https://github.com/holman/dotfiles), with private overrides inspired by [thoughtbot's dotfiles](https://github.com/thoughtbot/dotfiles). [chezmoi](https://www.chezmoi.io/user-guide/setup/) was also reviewed; this setup stays small enough to use a standard-library installer without another manager.

Configuration and scripts are MIT licensed; wallpaper artwork is excluded (see [asset notes](wallpapers/README.md)). Review and adapt the configuration before installing it on another machine.
