import enum
import yargy
import unittest
import collections


class FactParserTestCase(unittest.TestCase):

    def test_simple_rules(self):
        text = "газета «Коммерсантъ» сообщила ..."
        parser = yargy.FactParser()
        results = parser.parse(text, (
            ("word", {}),
            ("quote", {}),
            ("word", {}),
            ("quote", {}),
            ("$", {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['газета', '«', 'Коммерсантъ', '»'])

    def test_repeat_rules(self):
        text = "... ООО «Коммерсантъ КАРТОТЕКА» уполномочено ..."
        parser = yargy.FactParser()
        results = parser.parse(text, (
            ("quote", {}),
            ("word", {"repeat": True}),
            ("quote", {}),
            ("$", {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['«', 'Коммерсантъ', 'КАРТОТЕКА', '»'])

    def test_gram_label(self):
        text = "маленький принц красиво пел"
        parser = yargy.FactParser()
        results = parser.parse(text, (
            ("word", {"labels": [("gram", "ADJS")]}),
            ("word", {"labels": [("gram", "VERB")]}),
            ("$", {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['красиво', 'пел'])

    def test_gram_not_label(self):
        text = "Иван выпил чаю. И ушел."
        parser = yargy.FactParser()
        results = parser.parse(text, (
            ("word", {"labels": [("gram", "Name"), ("gram-not", "Abbr")]}),
            ("word", {"labels": [("gram", "VERB")]}),
            ("$", {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['Иван', 'выпил'])

    def test_gender_match_label(self):
        text = "Иван выпил чаю. Вика был красивый."
        rules = (
            ("word", {"labels": [("gram", "NOUN")]}),
            ("word", {"labels": [("gram", "VERB"), ("gender-match", 0)]}),
            ("$", {})
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
            ("word", {"labels": [("gram", "NOUN")]}),
            ("word", {"labels": [("gram", "VERB"), ("number-match", 0)]}),
            ("$", {})
        )
        parser = yargy.FactParser()
        results = parser.parse(text, rules)
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['саша', 'пилил'])

    def test_optional_rules(self):
        text = "новгород великий, москва."
        parser = yargy.FactParser()
        results = parser.parse(text, (
            ("word", {"labels": [("gram", "NOUN"), ("gram", "Geox")]}),
            ("word", {"labels": [("gram", "ADJF")], "optional": True}),
            ("$", {}))
        )
        self.assertEqual([[w[1] for w in n] for n in results], [['новгород', 'великий'], ['москва']])
        
        text = "иван иванович иванов, анна смирнова"
        parser = yargy.FactParser()
        results = parser.parse(text, (
            ("word", {"labels": [("gram", "NOUN"), ("gram", "Name")]}),
            ("word", {"labels": [("gram", "NOUN"), ("gram", "Patr")], "optional": True}),
            ("word", {"labels": [("gram", "NOUN"), ("gram", "Surn")]}),
            ("$", {}))
        )
        self.assertEqual([[w[1] for w in n] for n in results], [['иван', 'иванович', 'иванов'], ['анна', 'смирнова']])

    def test_output_deque(self):
        text = "иван иванович иванов, анна смирнова"
        parser = yargy.FactParser()
        output = collections.deque()
        results = parser.parse(text, (
            ("word", {"labels": [("gram", "NOUN"), ("gram", "Name")]}),
            ("word", {"labels": [("gram", "NOUN"), ("gram", "Patr")]}),
            ("word", {"labels": [("gram", "NOUN"), ("gram", "Surn")]}),
            ("$", {})),
            output
        )
        self.assertEqual([[w[1] for w in n] for n in results], [['иван', 'иванович', 'иванов']])
        self.assertEqual([n[1] for n in output], [',', 'анна', 'смирнова'])

class CombinatorTestCase(unittest.TestCase):

    class Person(enum.Enum):

        Fullname = (
            ('word', {
                'labels': [
                    ('gram', 'Name'),
                ],
            }),
            ('word', {
                'labels': [
                    ('gram', 'Surn'),
                ],
            }),
            ('$', {}),
        )

        Firstname = (
            ('word', {
                'labels': [
                    ('gram', 'Name'),
                ],
            }),
            ('$', {}),
        )

    class City(enum.Enum):

        Default = (
            ('word', {
                'labels': [
                    ('gram', 'Name'),
                ],
            }),
            ('$', {}),
        )

    def test_resolve_matches(self):
        text = 'владимир путин приехал в владимир'
        combinator = yargy.Combinator([self.Person, self.City])
        matches = list(combinator.extract(text))
        self.assertEqual(len(matches), 5)
        matches = combinator.resolve_matches(matches)
        self.assertEqual([match[1] for match in matches], ['Default', 'Fullname'])
