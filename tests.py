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

    def test_gram_label(self):
        text = "маленький принц красиво пел"
        parser = yargy.FactParser((
            ("word", {"labels": [{"gram": "ADJS"}]}),
            ("word", {"labels": [{"gram": "VERB"}]}),
            ("$", {}))
        )
        results = parser.parse(text)
        self.assertEqual(sum([[w.tail[0] for w in n] for n in results], []), ['красиво', 'пел'])

