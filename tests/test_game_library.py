import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from game_library import install_html_game, installed_games, remove_game

class GameLibraryTests(unittest.TestCase):
    def setUp(self):
        self.ctx = tempfile.TemporaryDirectory()
        self.root = Path(self.ctx.name)
        self.library = self.root / 'library'

    def tearDown(self):
        self.ctx.cleanup()

    def test_single_html_import_launch_and_remove(self):
        game_file = self.root / 'Simple Game.html'
        game_file.write_text('<html><title>Test</title></html>', encoding='utf-8')
        game = install_html_game(game_file, data_dir=self.library)
        listing = installed_games(self.library)
        self.assertEqual(len(listing), 1)
        self.assertEqual(listing[0]['name'], 'Simple Game')
        self.assertTrue(Path(listing[0]['main']).is_file())
        remove_game(listing[0], self.library)
        self.assertEqual(installed_games(self.library), [])

    def test_zip_preserves_assets(self):
        path = self.root / 'Redder7.zip'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('game/index.html', '<img src="sprites/hit.png">')
            z.writestr('game/sprites/hit.png', b'PNG')
        game = install_html_game(path, 'Redder7: The Game', self.library)
        self.assertTrue((Path(game['path']) / 'game/sprites/hit.png').exists())
        self.assertEqual(installed_games(self.library)[0]['start'], 'game/index.html')

    def test_rejects_zip_traversal(self):
        bad = self.root / 'bad.zip'
        with zipfile.ZipFile(bad, 'w') as z:
            z.writestr('../outside.html', '<html>oops</html>')
        with self.assertRaises(ValueError):
            install_html_game(bad, data_dir=self.library)
        self.assertFalse((self.root / 'outside.html').exists())

    def test_duplicate_games_get_separate_folders(self):
        sample = self.root / 'test.html'
        sample.write_text('<html>Hi</html>', encoding='utf-8')
        install_html_game(sample, 'Test', self.library)
        install_html_game(sample, 'Test', self.library)
        self.assertEqual(len(installed_games(self.library)), 2)

    def test_rejects_non_html_archive(self):
        bad = self.root / 'no-html.zip'
        with zipfile.ZipFile(bad, 'w') as z:
            z.writestr('readme.txt', 'Not a game')
        with self.assertRaises(ValueError):
            install_html_game(bad, data_dir=self.library)

if __name__ == '__main__':
    unittest.main()
