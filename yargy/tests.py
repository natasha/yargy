import enum
import yargy
import unittest
import collections


from yargy.tokenizer import Token, Tokenizer
from yargy.pipeline import SimpleMatchPipeline


class TokenizerTestCase(unittest.TestCase):

    def setUp(self):
        self.tokenizer = Tokenizer()

    def test_match_words(self):
        text = 'москва - moscow'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0][0], Token.Word)
        self.assertEqual(tokens[1][0], Token.Punct)
        self.assertEqual(tokens[2][0], Token.Word)
        self.assertIn('Geox', tokens[0][3][0]['grammemes'])
        self.assertIn('LATN', tokens[2][3][0]['grammemes'])

    def test_match_float_range(self):
        text = '1.5 - 2.0%'
        type, value, *_ = next(self.tokenizer.transform(text))
        self.assertEqual(list(value), [1.5, 1.6, 1.7, 1.8, 1.9, 2.0])

    def test_match_simple_numbers(self):
        text = '12 - 22 -3.4 3,4 1.0 1.5 - 2.5'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 5)

    def test_space_separated_integers(self):
        text = 'Цена: 2 600 000'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[-1][1], 2600000)

    def test_match_quotes(self):
        text = '"\'«»'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 4)
        self.assertEqual([t[0] for t in tokens], [Token.Quote] * 4)

class FactParserTestCase(unittest.TestCase):

    def test_simple_rules(self):
        text = 'газета «Коммерсантъ» сообщила ...'
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (Token.Word, {}),
            (Token.Quote, {}),
            (Token.Word, {}),
            (Token.Quote, {}),
            (Token.Term, {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['газета', '«', 'Коммерсантъ', '»'])

    def test_repeat_rules(self):
        text = '... ООО «Коммерсантъ КАРТОТЕКА» уполномочено ...'
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (Token.Quote, {}),
            (Token.Word, {'repeat': True}),
            (Token.Quote, {}),
            (Token.Term, {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['«', 'Коммерсантъ', 'КАРТОТЕКА', '»'])

    def test_gram_label(self):
        text = 'маленький принц красиво пел'
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (Token.Word, {'labels': [('gram', 'ADJS')]}),
            (Token.Word, {'labels': [('gram', 'VERB')]}),
            (Token.Term, {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['красиво', 'пел'])

    def test_gram_not_label(self):
        text = 'Иван выпил чаю. И ушел.'
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (Token.Word, {'labels': [('gram', 'Name'), ('gram-not', 'Abbr')]}),
            (Token.Word, {'labels': [('gram', 'VERB')]}),
            (Token.Term, {}))
        )
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['Иван', 'выпил'])

    def test_gender_match_label(self):
        text = 'Иван выпил чаю. Вика был красивый.'
        rules = (
            (Token.Word, {'labels': [('gram', 'NOUN')]}),
            (Token.Word, {'labels': [('gram', 'VERB'), ('gender-match', 0)]}),
            (Token.Term, {})
        )
        parser = yargy.FactParser()
        results = parser.parse(text, rules)
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['Иван', 'выпил'])

        text = 'Дрова были сырыми, но мальчики распилили их.'
        results = parser.parse(text, rules)
        self.assertEqual([[w[1] for w in n] for n in results], [['Дрова', 'были'], ['мальчики', 'распилили']])

        text = 'Саша была красивой, а её брат Саша был сильным'
        results = parser.parse(text, rules)
        self.assertEqual([[w[1] for w in n] for n in results], [['Саша', 'была'], ['Саша', 'был']])

    def test_number_match_label(self):
        text = 'Дрова был, саша пилил.'
        rules = (
            (Token.Word, {'labels': [('gram', 'NOUN')]}),
            (Token.Word, {'labels': [('gram', 'VERB'), ('number-match', 0)]}),
            (Token.Term, {})
        )
        parser = yargy.FactParser()
        results = parser.parse(text, rules)
        self.assertEqual(sum([[w[1] for w in n] for n in results], []), ['саша', 'пилил'])

    def test_optional_rules(self):
        text = 'новгород великий, москва.'
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (Token.Word, {'labels': [('gram', 'NOUN'), ('gram', 'Geox')]}),
            (Token.Word, {'labels': [('gram', 'ADJF')], 'optional': True}),
            (Token.Term, {}))
        )
        self.assertEqual([[w[1] for w in n] for n in results], [['новгород', 'великий'], ['москва']])
        
        text = 'иван иванович иванов, анна смирнова'
        parser = yargy.FactParser()
        results = parser.parse(text, (
            (Token.Word, {'labels': [('gram', 'NOUN'), ('gram', 'Name')]}),
            (Token.Word, {'labels': [('gram', 'NOUN'), ('gram', 'Patr')], 'optional': True}),
            (Token.Word, {'labels': [('gram', 'NOUN'), ('gram', 'Surn')]}),
            (Token.Term, {}))
        )
        self.assertEqual([[w[1] for w in n] for n in results], [['иван', 'иванович', 'иванов'], ['анна', 'смирнова']])

    def test_output_deque(self):
        text = 'иван иванович иванов, анна смирнова'
        parser = yargy.FactParser()
        output = collections.deque()
        results = parser.parse(text, (
            (Token.Word, {'labels': [('gram', 'NOUN'), ('gram', 'Name')]}),
            (Token.Word, {'labels': [('gram', 'NOUN'), ('gram', 'Patr')]}),
            (Token.Word, {'labels': [('gram', 'NOUN'), ('gram', 'Surn')]}),
            (Token.Term, {})),
            output
        )
        self.assertEqual([[w[1] for w in n] for n in results], [['иван', 'иванович', 'иванов']])
        self.assertEqual([n[1] for n in output], [',', 'анна', 'смирнова'])

class CombinatorTestCase(unittest.TestCase):

    class Person(enum.Enum):

        Fullname = (
            (Token.Word, {
                'labels': [
                    ('gram', 'Name'),
                ],
            }),
            (Token.Word, {
                'labels': [
                    ('gram', 'Surn'),
                ],
            }),
            (Token.Term, {}),
        )

        Firstname = (
            (Token.Word, {
                'labels': [
                    ('gram', 'Name'),
                ],
            }),
            (Token.Term, {}),
        )

    class City(enum.Enum):

        Default = (
            (Token.Word, {
                'labels': [
                    ('gram', 'Name'),
                ],
            }),
            (Token.Term, {}),
        )

    def test_resolve_matches(self):
        text = 'владимир путин приехал в владимир'
        combinator = yargy.Combinator([self.Person, self.City])
        matches = list(combinator.extract(text))
        self.assertEqual(len(matches), 5)
        matches = combinator.resolve_matches(matches)
        self.assertEqual([match[1] for match in matches], ['Default', 'Fullname'])

class SimpleMatchPipelineTestCase(unittest.TestCase):

    def test_match(self):
        text = 'иван приехал в нижний новгород'
        tokenizer = Tokenizer()
        tokens = collections.deque(tokenizer.transform(text))
        pipeline = SimpleMatchPipeline(tokens, dictionary={
            'нижний новгород': ['Geox', 'City'],
        })
        while tokens:
            match, token = pipeline.get_match()
            if not match:
                token = tokens.popleft()
                continue
            else:
                self.assertEqual(token, (
                    Token.Word,
                    'нижний новгород',
                    (15, 30),
                    {'grammemes': ['Geox', 'City']}
                ))
