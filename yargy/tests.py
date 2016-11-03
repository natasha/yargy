# coding: utf-8
from __future__ import unicode_literals

import yargy
import datetime
import unittest
import collections


from yargy.parser import Grammar
from yargy.tokenizer import Token, Tokenizer


class TokenizerTestCase(unittest.TestCase):

    def setUp(self):
        self.tokenizer = Tokenizer()

    def test_match_words(self):
        text = 'москва - moscow'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertIn('NOUN', tokens[0].forms[0]['grammemes'])
        self.assertIn('PUNCT', tokens[1].forms[0]['grammemes'])
        self.assertIn('LATN', tokens[2].forms[0]['grammemes'])

    def test_match_float_range(self):
        text = '1.5 - 2.0%'
        value = next(self.tokenizer.transform(text))[0]
        self.assertEqual(list(value), [1.5, 1.6, 1.7, 1.8, 1.9, 2.0])

    def test_match_simple_numbers(self):
        text = '12 - 22 -3.4 3,4 1.0 1.5 - 2.5'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 5)

    def test_space_separated_integers(self):
        text = 'Цена: 2 600 000'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[-1].value, 2600000)

    def test_match_quotes(self):
        text = '"\'«»'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 4)
        self.assertEqual([t.value for t in tokens], ['"', "'", '«', '»'])


class FactParserTestCase(unittest.TestCase):

    def test_simple_rules(self):
        text = 'газета «Коммерсантъ» сообщила ...'
        parser = yargy.Parser([
            Grammar('test', [
                {'labels': [('dictionary', {'газета', })]},
                {'labels': [('eq', '«')]},
                {'labels': [('not-eq', '»')]},
                {'labels': [('eq', '»')]},
            ])
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['газета', '«', 'Коммерсантъ', '»'])

    def test_repeat_rules(self):
        text = '... ООО «Коммерсантъ КАРТОТЕКА» уполномочено ...'
        parser = yargy.Parser([
            Grammar('test', [
                {'labels': [('eq', '«')]},
                {'repeatable': True, 'labels': [('gram', 'NOUN')]},
                {'labels': [('eq', '»')]},
            ])
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['«', 'Коммерсантъ', 'КАРТОТЕКА', '»'])

    def test_gram_label(self):
        text = 'маленький принц красиво пел'
        parser = yargy.Parser([
            Grammar('test', [
                {'labels': [('gram', 'ADJS')]},
                {'labels': [('gram', 'VERB')]},
            ])
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['красиво', 'пел'])

    def test_gram_not_label(self):
        text = 'Иван выпил чаю. И ушел домой.'
        parser = yargy.Parser([
            Grammar('test', [
                {'labels': [('gram', 'Name'), ('gram-not', 'Abbr')]},
                {'labels': [('gram', 'VERB')]},
            ])
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['Иван', 'выпил'])

    def test_gender_match_label(self):
        text = 'Иван выпил чаю. Вика был красивый.'
        grammar = Grammar('test', [
            {'labels': [('gram', 'NOUN')]},
            {'labels': [('gram', 'VERB'), ('gender-match', 0)]},
        ])
        parser = yargy.Parser([grammar])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['Иван', 'выпил'])

        text = 'Дрова были сырыми, но мальчики распилили их.'
        results = parser.extract(text)
        self.assertEqual([[w.value for w in n] for (_, n) in results], [['Дрова', 'были'], ['мальчики', 'распилили']])

        text = 'Саша была красивой, а её брат Саша был сильным'
        results = parser.extract(text)
        self.assertEqual([[w.value for w in n] for (_, n) in results], [['Саша', 'была'], ['Саша', 'был']])

    def test_number_match_label(self):
        text = 'Дрова был, саша пилил.'
        grammar = Grammar('test', [
            {'labels': [('gram', 'NOUN')]},
            {'labels': [('gram', 'VERB'), ('number-match', 0)]},
        ])
        parser = yargy.Parser([grammar])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['саша', 'пилил'])

    def test_optional_rules(self):
        text = 'великий новгород, москва.'
        parser = yargy.Parser([Grammar('test', [
            {'labels': [('gram', 'ADJF')], 'optional': True},
            {'labels': [('gram', 'NOUN'), ('gram', 'Geox')]},
        ])])
        results = parser.extract(text)
        self.assertEqual([[w.value for w in n] for (_, n) in results], [['великий', 'новгород'], ['москва']])
        
        text = 'иван иванович иванов, анна смирнова'
        parser = yargy.Parser([Grammar('test', [
            {'labels': [('gram', 'NOUN'), ('gram', 'Name')]},
            {'labels': [('gram', 'NOUN'), ('gram', 'Patr')], 'optional': True},
            {'labels': [('gram', 'NOUN'), ('gram', 'Surn')]},
        ])])
        results = parser.extract(text)
        self.assertEqual([[w.value for w in n] for (_, n) in results], [['иван', 'иванович', 'иванов'], ['анна', 'смирнова']])

# class DictionaryMatchPipelineTestCase(unittest.TestCase):

#     def test_match(self):
#         text = 'иван приехал в нижний новгород'
#         tokenizer = Tokenizer()
#         tokens = collections.deque(tokenizer.transform(text))
#         pipeline = DictionaryMatchPipeline(dictionary={
#             'нижний_новгород': [{'grammemes': ['Geox', 'City'], 'normal_form': 'нижний новгород'}],
#         })
#         matches = []
#         while tokens:
#             match, token = pipeline.get_match(tokens)
#             if not match:
#                 token = tokens.popleft()
#                 continue
#             else:
#                 matches.append(token)
#         self.assertEqual(matches, [(
#             Token.Word,
#             'нижний_новгород',
#             (15, 30),
#             [{'grammemes': ['Geox', 'City'], 'normal_form': 'нижний новгород'}]
#         )])

#     def test_match_in_different_form(self):
#         text = 'в нижнем новгороде прошел ещё один день'
#         tokenizer = Tokenizer()
#         tokens = collections.deque(tokenizer.transform(text))
#         pipeline = DictionaryMatchPipeline(dictionary={
#             'нижний_новгород': [{'grammemes': ['Geox', 'City'], 'normal_form': 'нижний новгород'}],
#         })
#         matches = []
#         while tokens:
#             match, token = pipeline.get_match(tokens)
#             if not match:
#                 token = tokens.popleft()
#                 continue
#             else:
#                 matches.append(token)
#         self.assertEqual(matches, [(
#             Token.Word,
#             'нижний_новгород',
#             (2, 18),
#             [{'grammemes': ['Geox', 'City'], 'normal_form': 'нижний новгород'}]
#         )])
