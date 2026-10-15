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


if __name__ == '__main__':
    unittest.main()
