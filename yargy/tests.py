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

    def test_repeat_rules(self):
        text = "... ООО «Коммерсантъ КАРТОТЕКА» уполномочено ..."
        parser = yargy.FactParser((
            ("quote", {}),
            ("word", {"repeat": True}),
            ("quote", {}),
            ("$", {}))
        )
        results = parser.parse(text)
        self.assertEqual(sum([[w.tail[0] for w in n] for n in results], []), ['«', 'Коммерсантъ', 'КАРТОТЕКА', '»'])


    def test_gram_label(self):
        text = "маленький принц красиво пел"
        parser = yargy.FactParser((
            ("word", {"labels": [{"gram": "ADJS"}]}),
            ("word", {"labels": [{"gram": "VERB"}]}),
            ("$", {}))
        )
        results = parser.parse(text)
        self.assertEqual(sum([[w.tail[0] for w in n] for n in results], []), ['красиво', 'пел'])

    def test_optional_rules(self):
        text = "великий новгород, москва."
        parser = yargy.FactParser((
            ("word", {"labels": [{"gram": "ADJF"}], "optional": True}),
            ("word", {"labels": [{"gram": "NOUN", "gram": "Geox"}]}),
            ("$", {}))
        )
        results = parser.parse(text)
        self.assertEqual([[w.tail[0] for w in n] for n in results], [['великий', 'новгород'], ['москва']])

