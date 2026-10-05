import tempfile
import unittest
from characters_unlimited.application import CharacterApplication


class PlayerScopeTests(unittest.TestCase):
    def test_coverage_excludes_only_named_optional_systems_and_keeps_construction(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
        options = {row['id']: row for row in view['options']}
        self.assertEqual({key for key, row in options.items() if row['scope'] == 'excluded'},
                         {'hu2-mega-hero', 'hu2-hardware-super-vehicle'})
        for key in ('hu2-robotics', 'hu2-bionics', 'hu2-robot-vehicle', 'hu2-robot-construction'):
            self.assertEqual(options[key]['scope'], 'included')
        self.assertEqual(view['summary']['excluded_options'], 2)
        self.assertEqual(view['summary']['in_scope_options'], 716)
        self.assertEqual(next(row for row in view['content_tickets'] if row['option_ids'] == ['hu2-mega-hero'])['scope'], 'excluded')
