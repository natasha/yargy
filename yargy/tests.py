import enum
import yargy
import unittest
import collections


class FactParserTestCase(unittest.TestCase):

    def test_simple_rules(self):
        text = "газета «Коммерсантъ» сообщила ..."
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (yargy.Token.Word, {}),
            (yargy.Token.Quote, {}),
            (yargy.Token.Word, {}),
            (yargy.Token.Quote, {}),
            (yargy.Token.Term, {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['газета', '«', 'Коммерсантъ', '»'])

    def test_repeat_rules(self):
        text = "... ООО «Коммерсантъ КАРТОТЕКА» уполномочено ..."
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (yargy.Token.Quote, {}),
            (yargy.Token.Word, {"repeat": True}),
            (yargy.Token.Quote, {}),
            (yargy.Token.Term, {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['«', 'Коммерсантъ', 'КАРТОТЕКА', '»'])

    def test_gram_label(self):
        text = "маленький принц красиво пел"
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (yargy.Token.Word, {"labels": [("gram", "ADJS")]}),
            (yargy.Token.Word, {"labels": [("gram", "VERB")]}),
            (yargy.Token.Term, {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['красиво', 'пел'])

    def test_gram_not_label(self):
        text = "Иван выпил чаю. И ушел."
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (yargy.Token.Word, {"labels": [("gram", "Name"), ("gram-not", "Abbr")]}),
            (yargy.Token.Word, {"labels": [("gram", "VERB")]}),
            (yargy.Token.Term, {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['Иван', 'выпил'])

    def test_gender_match_label(self):
        text = "Иван выпил чаю. Вика был красивый."
        rules = (
            (yargy.Token.Word, {"labels": [("gram", "NOUN")]}),
            (yargy.Token.Word, {"labels": [("gram", "VERB"), ("gender-match", 0)]}),
            (yargy.Token.Term, {})
        )
        parser = yargy.FactParser()
        results = parser.parse(text, rules)
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['Иван', 'выпил'])

        text = "Дрова были сырыми, но мальчики распилили их."
        results = parser.parse(text, rules)
        self.assertEqual([[w[1] for w in n] for n in results], [['Дрова', 'были'], ['мальчики', 'распилили']])

        text = "Саша была красивой, а её брат Саша был сильным"
        results = parser.parse(text, rules)
        self.assertEqual([[w[1] for w in n] for n in results], [['Саша', 'была'], ['Саша', 'был']])

    def test_number_match_label(self):
        text = "Дрова был, саша пилил."
        rules = (
            (yargy.Token.Word, {"labels": [("gram", "NOUN")]}),
            (yargy.Token.Word, {"labels": [("gram", "VERB"), ("number-match", 0)]}),
            (yargy.Token.Term, {})
        )
        parser = yargy.FactParser()
        results = parser.parse(text, rules)
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['саша', 'пилил'])

    def test_optional_rules(self):
        text = "новгород великий, москва."
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (yargy.Token.Word, {"labels": [("gram", "NOUN"), ("gram", "Geox")]}),
            (yargy.Token.Word, {"labels": [("gram", "ADJF")], "optional": True}),
            (yargy.Token.Term, {}))
        )
        self.assertEqual([[w[1] for w in n] for n in results], [['новгород', 'великий'], ['москва']])
        
        text = "иван иванович иванов, анна смирнова"
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (yargy.Token.Word, {"labels": [("gram", "NOUN"), ("gram", "Name")]}),
            (yargy.Token.Word, {"labels": [("gram", "NOUN"), ("gram", "Patr")], "optional": True}),
            (yargy.Token.Word, {"labels": [("gram", "NOUN"), ("gram", "Surn")]}),
            (yargy.Token.Term, {}))
        )
        self.assertEqual([[w[1] for w in n] for n in results], [['иван', 'иванович', 'иванов'], ['анна', 'смирнова']])

    def test_output_deque(self):
        text = "иван иванович иванов, анна смирнова"
        parser = yargy.FactParser()
        output = collections.deque()
        results = parser.parse(text, (
            (yargy.Token.Word, {"labels": [("gram", "NOUN"), ("gram", "Name")]}),
            (yargy.Token.Word, {"labels": [("gram", "NOUN"), ("gram", "Patr")]}),
            (yargy.Token.Word, {"labels": [("gram", "NOUN"), ("gram", "Surn")]}),
            (yargy.Token.Term, {})),
            output
        )
        self.assertEqual([[w[1] for w in n] for n in results], [['иван', 'иванович', 'иванов']])
        self.assertEqual([n[1] for n in output], [',', 'анна', 'смирнова'])

class CombinatorTestCase(unittest.TestCase):

    class Person(enum.Enum):

        Fullname = (
            (yargy.Token.Word, {
                'labels': [
                    ('gram', 'Name'),
                ],
            }),
            (yargy.Token.Word, {
                'labels': [
                    ('gram', 'Surn'),
                ],
            }),
            (yargy.Token.Term, {}),
        )

        Firstname = (
            (yargy.Token.Word, {
                'labels': [
                    ('gram', 'Name'),
                ],
            }),
            (yargy.Token.Term, {}),
        )

    class City(enum.Enum):

        Default = (
            (yargy.Token.Word, {
                'labels': [
                    ('gram', 'Name'),
                ],
            }),
            (yargy.Token.Term, {}),
        )

    def test_resolve_matches(self):
        text = 'владимир путин приехал в владимир'
        combinator = yargy.Combinator([self.Person, self.City])
        matches = list(combinator.extract(text))
        self.assertEqual(len(matches), 5)
        matches = combinator.resolve_matches(matches)
        self.assertEqual([match[1] for match in matches], ['Default', 'Fullname'])
