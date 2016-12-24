# coding: utf-8
from __future__ import unicode_literals

import enum
import os.path
import datetime
import unittest
import collections


from yargy.parser import Grammar, Parser, Combinator
from yargy.labels import (
    and_,
    or_,
    gram,
    gram_not,
    gram_any,
    dictionary,
    eq,
    not_eq,
    gender_match,
    number_match,
    gnc_match,
)
from yargy.tokenizer import Token, Tokenizer
from yargy.pipeline import (
    DictionaryPipeline,
    CustomGrammemesPipeline,
)
from yargy.utils import (
    get_original_text,
    get_normalized_text,
)


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
        value = next(self.tokenizer.transform(text)).value
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
        text = '"\'«»„“'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 6)
        self.assertEqual([t.value for t in tokens], ['"', "'", '«', '»', '„', '“'])
        self.assertEqual([t.forms[0]['grammemes'] for t in tokens], [
            {'QUOTE'},
            {'QUOTE'},
            {'QUOTE', 'L-QUOTE'},
            {'QUOTE', 'R-QUOTE'},
            {'QUOTE', 'L-QUOTE'},
            {'QUOTE', 'R-QUOTE'},
        ])

    def test_match_float_range_with_commas(self):
        text = "1,5-2,5 года"
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 2)
        self.assertEqual([t.forms[0] for t in tokens], [
            {'grammemes': {'RANGE', 'FLOAT-RANGE'}, 'normal_form': '1,5-2,5'},
            {'grammemes': {'inan', 'masc', 'sing', 'NOUN', 'gent'}, 'normal_form': 'год'},
        ])

    def test_match_roman_number(self):
        text = 'XX век Fox'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertEqual([t.forms[0] for t in tokens], [
            {'grammemes': {'ROMN'}, 'normal_form': 'XX'},
            {'grammemes': {'ADVB'}, 'normal_form': 'век'},
            {'grammemes': {'LATN'}, 'normal_form': 'fox'},
        ])

    def test_match_email_address(self):
        text = 'напиши на example@example.com'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertEqual([t.forms[0] for t in tokens], [
            {'grammemes': {'perf', 'tran', 'sing', 'excl', 'impr', 'VERB'}, 'normal_form': 'написать'},
            {'grammemes': {'PREP'}, 'normal_form': 'на'},
            {'grammemes': {'EMAIL'}, 'normal_form': 'example@example.com'}
        ])

    def test_match_phone_number(self):
        self.maxDiff = None
        text = 'отдых 24 часа +7-812-999-9999 / 89818210000 / +7-(999)-999-99-99'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 8)
        self.assertEqual([t.value for t in tokens], [
            'отдых',
            24,
            'часа',
            '+7-812-999-9999',
            '/',
            '89818210000',
            '/',
            '+7-(999)-999-99-99',
        ])


class UtilsTestCase(unittest.TestCase):

    def setUp(self):
        self.person_grammar = Grammar('person', [
            {
                'labels': [
                    gram('Name'),
                ],
            },
            {
                'labels': [
                    gram('Surn'),
                    gnc_match(-1, solve_disambiguation=True),
                ],
            },
        ])
        self.parser = Parser(grammars=[
            self.person_grammar,
        ])
        self.person_text = 'ивану иванову было скучно'

    def test_get_original_text(self):
        grammar, tokens = next(
            self.parser.extract(
                self.person_text,
            )
        )
        original_text = get_original_text(self.person_text, tokens)
        self.assertEqual(original_text, 'ивану иванову')

    def test_get_normalized_text(self):
        grammar, tokens = next(
            self.parser.extract(
                self.person_text,
            )
        )
        original_text = get_normalized_text(tokens)
        self.assertEqual(original_text, 'иван иванов')


class FactParserTestCase(unittest.TestCase):

    def test_simple_rules(self):
        text = 'газета «Коммерсантъ» сообщила ...'
        parser = Parser([
            Grammar('test', [
                {'labels': [dictionary({'газета', })]},
                {'labels': [eq('«')]},
                {'labels': [not_eq('»')]},
                {'labels': [eq('»')]},
            ])
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['газета', '«', 'Коммерсантъ', '»'])

    def test_repeat_rules(self):
        text = '... ООО «Коммерсантъ КАРТОТЕКА» уполномочено ...'
        parser = Parser([
            Grammar('test', [
                {'labels': [eq('«')]},
                {'repeatable': True, 'labels': [gram('NOUN')]},
                {'labels': [eq('»')]},
            ])
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['«', 'Коммерсантъ', 'КАРТОТЕКА', '»'])

    def test_and_or_label(self):
        text = 'кузявые бутявки и ...'
        parser = Parser([
            Grammar('test', [
                {
                    'labels': [
                        and_((
                            or_((
                                gram('ADJF'),
                                gram('NOUN'),
                            )),
                            gram_not('Abbr'),
                        )),
                    ],
                },
            ]),
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['кузявые', 'бутявки'])

    def test_gram_label(self):
        text = 'маленький принц красиво пел'
        parser = Parser([
            Grammar('test', [
                {'labels': [gram('ADJS')]},
                {'labels': [gram('VERB')]},
            ])
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['красиво', 'пел'])

    def test_gram_not_label(self):
        text = 'Иван выпил чаю. И ушел домой.'
        parser = Parser([
            Grammar('test', [
                {'labels': [gram('Name'), gram_not('Abbr')]},
                {'labels': [gram('VERB')]},
            ])
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['Иван', 'выпил'])

    def test_gender_match_label(self):
        text = 'Иван выпил чаю. Вика был красивый.'
        grammar = Grammar('test', [
            {'labels': [gram('NOUN')]},
            {'labels': [gram('VERB'), gender_match(0)]},
        ])
        parser = Parser([grammar])
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
            {'labels': [gram('NOUN')]},
            {'labels': [gram('VERB'), number_match(0)]},
        ])
        parser = Parser([grammar])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['саша', 'пилил'])

    def test_optional_rules(self):
        text = 'великий новгород, москва.'
        parser = Parser([Grammar('test', [
            {'labels': [gram('ADJF')], 'optional': True},
            {'labels': [gram('NOUN'), gram('Geox')]},
        ])])
        results = parser.extract(text)
        self.assertEqual([[w.value for w in n] for (_, n) in results], [['великий', 'новгород'], ['москва']])

        text = 'иван иванович иванов, анна смирнова'
        parser = Parser([Grammar('test', [
            {'labels': [gram('NOUN'), gram('Name')]},
            {'labels': [gram('NOUN'), gram('Patr')], 'optional': True},
            {'labels': [gram('NOUN'), gram('Surn')]},
        ])])
        results = parser.extract(text)
        self.assertEqual([[w.value for w in n] for (_, n) in results], [['иван', 'иванович', 'иванов'], ['анна', 'смирнова']])

    def test_skip_rules(self):
        text = 'улица академика павлова, дом 7'
        parser = Parser([
            Grammar('street', [
                {'labels': [
                    dictionary({'улица', }),
                ]},
                {'labels': [
                    gram_any({'accs', }),
                ], 'repeatable': True},
                {'labels': [
                    gram('PUNCT'),
                ], 'skip': True},
                {'labels': [
                    dictionary({'дом', }),
                ], 'skip': True},
                {'labels': [
                    gram('NUMBER'),
                ]},
            ]),
        ])
        results = parser.extract(text)
        self.assertEqual(sum([[w.value for w in n] for (_, n) in results], []), ['улица', 'академика', 'павлова', 7])

    def test_solve_disambiguation(self):
        text = 'саше иванову, саша иванова, сашу иванову, сашу иванова'
        grammar = Grammar('Firstname_and_Lastname', [
                {
                    'labels': [
                        gram('Name'),
                    ],
                },
                {
                    'labels': [
                        gram('Surn'),
                        gnc_match(-1, solve_disambiguation=True, match_all_disambiguation_forms=False),
                    ],
                },
            ], changes_token_structure=True)
        parser = Parser([
            grammar,
        ])
        results = parser.extract(text)
        self.assertEqual(list(results), [
            (grammar,
                [
                    Token('саше', (0, 4), [{'grammemes': {'femn', 'anim', 'sing', 'Ms-f', 'Name', 'NOUN', 'datv'}, 'normal_form': 'саша'}]),
                    Token('иванову', (5, 12), [{'grammemes': {'anim', 'Surn', 'Sgtm', 'sing', 'NOUN', 'datv', 'masc'}, 'normal_form': 'иванов'}])
                ]
            ),
            (grammar,
                [
                    Token('саша', (14, 18), [{'grammemes': {'femn', 'anim', 'nomn', 'sing', 'Ms-f', 'NOUN', 'Name'}, 'normal_form': 'саша'}]),
                    Token('иванова', (19, 26), [{'grammemes': {'femn', 'anim', 'nomn', 'Surn', 'Sgtm', 'sing', 'NOUN'}, 'normal_form': 'иванов'}])
                ]
            ),
            (grammar,
                [
                    Token('сашу', (28, 32), [{'grammemes': {'accs', 'femn', 'anim', 'sing', 'Ms-f', 'NOUN', 'Name'}, 'normal_form': 'саша'}]),
                    Token('иванову', (33, 40), [{'grammemes': {'accs', 'femn', 'anim', 'Surn', 'Sgtm', 'sing', 'NOUN'}, 'normal_form': 'иванов'}])
                ]
            ),
            (grammar,
                [
                    Token('сашу', (42, 46), [{'grammemes': {'accs', 'femn', 'anim', 'sing', 'Ms-f', 'NOUN', 'Name'}, 'normal_form': 'саша'}]),
                    Token('иванова', (47, 54), [{'grammemes': {'accs', 'anim', 'Surn', 'Sgtm', 'sing', 'NOUN', 'masc'}, 'normal_form': 'иванов'}])
                ]
            )
        ])

class DictionaryPipelineTestCase(unittest.TestCase):

    def test_match(self):
        text = 'иван приехал в нижний новгород'
        tokenizer = Tokenizer()
        tokens = tokenizer.transform(text)
        pipeline = DictionaryPipeline(dictionary={
            'нижний_новгород': [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}],
        })
        stream = pipeline(tokens)
        matches = []
        while True:
            try:
                token = next(stream)
            except StopIteration:
                break
            if token.value != 'нижний_новгород':
                continue
            else:
                matches.append(token)
        self.assertEqual(matches, [Token(
            'нижний_новгород',
            (15, 30),
            [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}]
        )])

    def test_match_in_different_form(self):
        text = 'в нижнем новгороде прошел ещё один день'
        tokenizer = Tokenizer()
        tokens = tokenizer.transform(text)
        pipeline = DictionaryPipeline(dictionary={
            'нижний_новгород': [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}],
        })
        stream = pipeline(tokens)
        matches = []
        while True:
            try:
                token = next(pipeline)
            except StopIteration:
                break
            if token.value != 'нижнем_новгороде':
                continue
            else:
                matches.append(token)
        self.assertEqual(matches, [Token(
            'нижнем_новгороде',
            (2, 18),
            [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}]
        )])

    def test_match_with_parser(self):
        text = 'в нижнем новгороде прошел ещё один день'
        pipeline = DictionaryPipeline(dictionary={
            'нижний_новгород': [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}],
        })
        parser = Parser([
            Grammar('city', [
                {'labels': [
                    gram('Geox/City'),
                ]},
            ]),
        ], pipelines=[pipeline])
        results = parser.extract(text)
        _, matches = next(results)
        self.assertEqual(matches, [Token(
            'нижнем_новгороде',
            (2, 18),
            [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}]
        )])

    def test_custom_grammemes_pipeline(self):
        text = 'группой компаний или торговым домом'

        class OrganisationTypePipeline(CustomGrammemesPipeline):

            Grammemes = {
                'Orgn/Type',
            }

            Dictionary = {
                'группа_компания',
                'торговый_дом',
            }

            Path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'testdata/orgn_type.dawg',
            )

        grammar = Grammar('organisation_type', [
            {
                'labels': [
                    gram('Orgn/Type'),
                ]
            },
        ])
        parser = Parser([
            grammar,
        ], pipelines=[
            OrganisationTypePipeline(),
        ])
        results = parser.extract(text)
        self.assertEqual(list(results), [
        (grammar,
            [Token('группой_компаний', (0, 16), [{'normal_form': 'группа_компания', 'grammemes': {'Orgn/Type'}}])]),
        (grammar,
            [Token('торговым_домом', (21, 35), [{'normal_form': 'торговый_дом', 'grammemes': {'Orgn/Type'}}])])
        ])


class CombinatorTestCase(unittest.TestCase):

    class Person(enum.Enum):

        Fullname = [
            {
                'labels': [
                    gram('Name'),
                ],
            },
            {
                'labels': [
                    gram('Surn'),
                ],
            },
        ]

        Firstname = [
            {
                'labels': [
                    gram('Name'),
                ],
            },
        ]

    class City(enum.Enum):

        Default = [
            {
                'labels': [
                    gram('Name'),
                ],
            },
        ]

    class Money(enum.Enum):

        Simple = [
            {
                'labels': [
                    gram('NUMBER'),
                ],
            },
            {
                'labels': [
                    dictionary({
                        'рубль',
                        'евро',
                        'доллар',
                    }),
                ],
            },
        ]

    def test_extract(self):
        text = '600 рублей или 10 долларов'
        combinator = Combinator([self.Money])
        matches = list(combinator.extract(text))
        for match in matches:
            self.assertEqual(match[0], self.Money.Simple)
            self.assertEqual(type(match[1][0].value), int)

    def test_resolve_matches(self):
        text = 'владимир путин приехал в владимир'
        combinator = Combinator([self.Person, self.City])
        matches = list(combinator.extract(text))
        self.assertEqual(len(matches), 5)
        matches = combinator.resolve_matches(matches)
        matched_rules = [match[0] for match in matches]
        self.assertIn(self.Person.Fullname, matched_rules)
        self.assertIn(self.City.Default, matched_rules)
