import yargy
import unittest


class FactParserTestCase(unittest.TestCase):

    def test_simple_rules(self):
        text = "газета «Коммерсантъ» сообщила ..."
        parser = yargy.FactParser((
            ("word", {}),
            ("quote", {}),
            ("word", {}),
            ("quote", {}),
            ("$", {}))
        )
        results = parser.parse(text)
        self.assertEqual(sum([[w.tail[0] for w in n] for n in results], []), ['газета', '«', 'Коммерсантъ', '»'])
