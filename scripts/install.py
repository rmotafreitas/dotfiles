#!/usr/bin/env python3
"""Preview or symlink the explicitly tracked home/ files; back up conflicts."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = ('.bashrc', '.profile', '.zshenv', '.zshrc', '.gitconfig', '.tmux.conf',
         '.config/shell/toolchain.sh', '.config/shell/aliases.sh')
# (source under macos/, target relative to home); linked only on macOS.
MACOS_FILES = (('home/.bash_profile', '.bash_profile'), ('home/.zprofile', '.zprofile'),
               ('home/.p10k.zsh', '.p10k.zsh'),
               ('home/.config/shell/macos.sh', '.config/shell/macos.sh'),
               ('home/.config/zsh/macos-pre.zsh', '.config/zsh/macos-pre.zsh'),
               ('home/.config/zsh/macos.zsh', '.config/zsh/macos.zsh'),
               ('ghostty/config.ghostty', 'Library/Application Support/com.mitchellh.ghostty/config.ghostty'))

WALLPAPERS = ('02rz3dw29c2h1_upscaled.jpeg', 'wallhaven-9o927x_3840x2160.png',
              'wallhaven-qrgqyq_3840x2160.png')


def install(home: Path, apply: bool, wallpapers: bool = False, platform: str = 'auto') -> None:
    home = home.expanduser().absolute()
    backup = home / '.local/state/dotfiles/backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    entries = [(ROOT / 'home' / name, Path(name)) for name in FILES]
    if platform == 'auto':
        platform = 'darwin' if sys.platform == 'darwin' else 'linux'
    if platform == 'darwin':
        entries += [(ROOT / 'macos' / source, Path(target)) for source, target in MACOS_FILES]
    if wallpapers:
        entries += [(ROOT / 'wallpapers' / name, Path('Pictures/Wallpapers') / name) for name in WALLPAPERS]
    for source, relative in entries:
        target = home / relative
        if target.is_symlink() and target.resolve() == source:
            print(f'Already linked: {relative}')
            continue
        # Reject a parent symlink that would send writes outside the chosen home.
        if not target.parent.resolve().is_relative_to(home.resolve()):
            raise SystemExit(f'Refusing destination outside home: {target}')
        exists = target.exists() or target.is_symlink()
        print(f'{"Back up and link" if exists else "Link"}: {relative}')
        if not apply:
            continue
        if exists:
            # Preserve existing identity/helpers locally when adopting Git config.
            local_git = home / '.gitconfig.local'
            if relative == Path('.gitconfig') and target.is_file() and not (local_git.exists() or local_git.is_symlink()):
                shutil.copy2(target, local_git)
                local_git.chmod(0o600)
            backup.mkdir(parents=True, exist_ok=True, mode=0o700)
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(saved))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source)
    if backup.exists():
        print(f'Backups: {backup}')
    if not apply:
        print('Preview only. Add --apply to install.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='apply the previewed symlinks')
    parser.add_argument('--home', type=Path, default=Path.home(), help='alternate home for testing')
    parser.add_argument('--wallpapers', action='store_true', help='also link the wallpaper collection into Pictures/Wallpapers')
    parser.add_argument('--platform', choices=('auto', 'linux', 'darwin'), default='auto', help='link macOS files too (default: detect)')
    args = parser.parse_args()
    install(args.home, args.apply, args.wallpapers, args.platform)
