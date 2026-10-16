import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / 'scripts/install.py'


class DotfilesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)

    def install(self, *flags):
        return subprocess.run([sys.executable, str(INSTALL), '--home', str(self.home), *flags], check=True, capture_output=True, text=True)

    def test_preview_does_not_write(self):
        self.install()
        self.assertEqual(list(self.home.iterdir()), [])

    def test_backup_identity_and_idempotence(self):
        (self.home / '.bashrc').write_text('# original\n')
        identity = '[user]\n name = Example\n email = example@example.invalid\n'
        (self.home / '.gitconfig').write_text(identity)
        self.install('--apply')
        self.assertTrue((self.home / '.bashrc').is_symlink())
        self.assertEqual((self.home / '.gitconfig.local').read_text(), identity)
        backups = list((self.home / '.local/state/dotfiles/backups').iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / '.bashrc').read_text(), '# original\n')
        self.install('--apply')
        self.assertEqual(list((self.home / '.local/state/dotfiles/backups').iterdir()), backups)

    def test_optional_wallpapers_preserve_other_pictures(self):
        pictures = self.home / 'Pictures'
        pictures.mkdir()
        (pictures / 'personal.txt').write_text('keep')
        self.install('--apply')
        self.assertFalse((pictures / 'Wallpapers').exists())
        self.install('--wallpapers')
        self.assertFalse((pictures / 'Wallpapers').exists())
        self.install('--apply', '--wallpapers')
        links = list((pictures / 'Wallpapers').iterdir())
        self.assertEqual(len(links), 3)
        self.assertTrue(all(p.is_symlink() and p.resolve().is_file() for p in links))
        self.assertEqual((pictures / 'personal.txt').read_text(), 'keep')
        self.install('--apply', '--wallpapers')
        self.assertFalse((self.home / '.local/state/dotfiles/backups').exists())

    def test_external_parent_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.home / '.config').symlink_to(outside)
            result = subprocess.run([sys.executable, str(INSTALL), '--home', str(self.home)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_shells_without_optional_tools_and_with_java_override(self):
        self.install('--apply')
        java = self.home / 'custom-jdk'
        (java / 'bin').mkdir(parents=True)
        (java / 'bin/java').write_text('#!/bin/sh\nexit 0\n')
        (java / 'bin/java').chmod(0o755)
        (self.home / 'Android/Sdk/platform-tools').mkdir(parents=True)
        env = {'HOME': str(self.home), 'PATH': '/usr/bin:/bin:/usr/bin', 'TERM': 'dumb', 'JAVA_HOME': str(java)}
        probe = 'test "$JAVA_HOME/bin/java" = "$(command -v java)" && test "$ANDROID_HOME" = "$HOME/Android/Sdk" && test "$ANDROID_HOME" = "$ANDROID_SDK_ROOT"'
        for shell in ['bash', 'zsh']:
            if not shutil.which(shell):
                self.skipTest(f'{shell} is not installed')
            command = '. "$HOME/.config/shell/toolchain.sh"; ' + probe
            subprocess.run([shell, '-c', command], env=env, check=True, capture_output=True)
            subprocess.run([shell, '-ic', 'exit 0'], env=env, check=True, capture_output=True)
        # Sources are idempotent and explicit toolchain paths win.
        command = '. "$HOME/.config/shell/toolchain.sh"; before=$PATH; . "$HOME/.config/shell/toolchain.sh"; test "$before" = "$PATH"'
        subprocess.run(['bash', '-c', command], env=env, check=True)

    def shell_env(self, **extra):
        return {'HOME': str(self.home), 'PATH': '/usr/bin:/bin', 'TERM': 'dumb', **extra}

    def test_macos_files_are_linked_only_on_macos(self):
        self.install('--apply', '--platform', 'linux')
        self.assertFalse((self.home / '.zprofile').exists())
        self.assertFalse((self.home / '.config/shell/macos.sh').exists())
        self.install('--apply', '--platform', 'darwin')
        for name in ['.zprofile', '.bash_profile', '.p10k.zsh', '.config/shell/macos.sh',
                     '.config/zsh/macos-pre.zsh', '.config/zsh/macos.zsh',
                     'Library/Application Support/com.mitchellh.ghostty/config.ghostty']:
            self.assertTrue((self.home / name).is_symlink() and (self.home / name).resolve().is_file(), name)
        self.assertFalse((self.home / '.local/state/dotfiles/backups').exists())

    def test_macos_shells_start_without_optional_tools(self):
        self.install('--apply', '--platform', 'darwin')
        for shell in ['bash', 'zsh']:
            if not shutil.which(shell):
                self.skipTest(f'{shell} is not installed')
            for flags in ['-c', '-ic', '-lic']:
                subprocess.run([shell, flags, 'exit 0'], env=self.shell_env(), check=True, capture_output=True)

    def test_zprofile_restores_toolchain_precedence_after_path_rewrite(self):
        if not shutil.which('zsh'):
            self.skipTest('zsh is not installed')
        self.install('--apply', '--platform', 'darwin')
        java = self.home / 'custom-jdk'
        (java / 'bin').mkdir(parents=True)
        (java / 'bin/java').write_text('#!/bin/sh\nexit 0\n')
        (java / 'bin/java').chmod(0o755)
        # path_helper puts system directories first; .zprofile must undo that.
        command = ('. "$HOME/.config/shell/toolchain.sh"; PATH="/usr/bin:/bin:$PATH"; '
                   '. "$HOME/.zprofile"; test "$JAVA_HOME/bin/java" = "$(command -v java)" && '
                   'test "$(printf %s "$PATH" | tr : "\\n" | sort | uniq -d)" = ""')
        subprocess.run(['zsh', '-c', command], env=self.shell_env(JAVA_HOME=str(java)), check=True, capture_output=True)

    def test_macos_zsh_prelude_selects_installed_theme_and_plugins(self):
        if not shutil.which('zsh'):
            self.skipTest('zsh is not installed')
        self.install('--apply', '--platform', 'darwin')
        probe = '. "$HOME/.config/zsh/macos-pre.zsh"; print -r -- "[$DOTFILES_ZSH_THEME][$dotfiles_plugins]"'
        run = lambda: subprocess.run(['zsh', '-c', probe], env=self.shell_env(), check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(run(), '[][]')
        omz = self.home / '.oh-my-zsh'
        (omz / 'custom/themes/powerlevel10k').mkdir(parents=True)
        (omz / 'custom/themes/powerlevel10k/powerlevel10k.zsh-theme').write_text('')
        (omz / 'plugins/macos').mkdir(parents=True)
        self.assertEqual(run(), '[powerlevel10k/powerlevel10k][macos]')
        # The shared .zshrc starts with the theme and plugins selected.
        subprocess.run(['zsh', '-ic', 'exit 0'], env=self.shell_env(), check=True, capture_output=True)

    def test_sdkman_is_skipped_on_bash_older_than_4(self):
        self.install('--apply')
        init = self.home / '.sdkman/bin/sdkman-init.sh'
        init.parent.mkdir(parents=True)
        init.write_text('touch "$HOME/sdkman-loaded"\n')
        loaded = self.home / 'sdkman-loaded'
        run = lambda version: subprocess.run(
            ['bash', '-c', f'BASH_VERSION="{version}"; . "$HOME/.config/shell/toolchain.sh"'],
            env=self.shell_env(), check=True, capture_output=True, stdin=subprocess.DEVNULL)
        run('3.2.57(1)-release')
        self.assertFalse(loaded.exists())
        run('5.3.15(1)-release')
        self.assertTrue(loaded.exists())

    def test_bash_has_colors_unless_no_color_is_set(self):
        self.install('--apply')
        probe = 'echo "$CLICOLOR"; type -t ls; echo "$PS1"'
        run = lambda **extra: subprocess.run(['bash', '-ic', probe], env=self.shell_env(**extra), check=True, capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout
        colored = run()
        self.assertIn('1\nalias\n', colored)
        self.assertIn('\\e[32m', colored)
        plain = run(NO_COLOR='1')
        self.assertNotIn('alias', plain.split('\n')[1])
        self.assertNotIn('\\e[', plain)

    def test_unknown_ghostty_terminal_falls_back_to_xterm_256color(self):
        self.install('--apply')
        for shell in ['bash', 'zsh']:
            if not shutil.which(shell):
                self.skipTest(f'{shell} is not installed')
            term = lambda value: subprocess.run([shell, '-c', '. "$HOME/.config/shell/toolchain.sh"; echo "$TERM"'],
                                                env=self.shell_env(TERM=value), check=True, capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout.strip()
            self.assertEqual(term('xterm-ghostty'), 'xterm-256color')
            self.assertEqual(term('screen-256color'), 'screen-256color')

    def test_startup_fastfetch_keeps_colors_during_the_instant_prompt(self):
        if not shutil.which('zsh'):
            self.skipTest('zsh is not installed')
        self.install('--apply', '--platform', 'darwin')
        fake = self.home / 'bin/fastfetch'
        fake.parent.mkdir()
        fake.write_text('#!/bin/sh\necho "$@" > "$HOME/fastfetch-args"\n')
        fake.chmod(0o755)
        subprocess.run(['zsh', '-ic', '_fastfetch_once'], env=self.shell_env(), check=True, capture_output=True, stdin=subprocess.DEVNULL)
        # stdout is not a terminal here, like during the instant prompt; colors must be forced.
        self.assertEqual((self.home / 'fastfetch-args').read_text().strip(), '--pipe false')


if __name__ == '__main__':
    unittest.main()
