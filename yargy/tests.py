# coding: utf-8
from __future__ import unicode_literals

import sys
import enum
import os.path
import platform
import datetime
import unittest
import itertools
import collections

from yargy.compat import str
from yargy.parser import Grammar, Parser, Combinator, Operation, OR
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
from yargy.normalization import (
    NormalizationType,
    get_normalized_text,
)
from yargy.interpretation import (
    InterpretationObject,
    InterpretationEngine,
)

from yargy.utils import (
    get_original_text,
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

    @unittest.skipIf(sys.version_info.major < 3, 'python 2 creates different objects for same xrange calls')
    @unittest.skipIf(platform.python_implementation() == 'PyPy', 'pypy & pypy3 have same semantics for range objects')
    def test_match_simple_numbers(self):
        text = '12 - 22 -3.4 3,4 1.0 1.5 - 2.5'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 5)
        self.assertEqual([t.value for t in tokens][:4], [range(12, 22), -3.4, 3.4, 1.0])

    def test_space_separated_integers(self):
        text = 'Цена: 2 600 000'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[-1].value, 2600000)

    def test_match_quotes(self):
        text = '"\'«»„“'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual([t.value for t in tokens], ['"', "'", '«', '»', '„', '“'])
        self.assertEqual([t.forms[0]['grammemes'] for t in tokens], [
            {'QUOTE', 'G-QUOTE'},
            {'QUOTE', 'G-QUOTE'},
            {'QUOTE', 'L-QUOTE'},
            {'QUOTE', 'R-QUOTE'},
            {'QUOTE', 'L-QUOTE'},
            {'QUOTE', 'R-QUOTE'},
        ])

    def test_match_float_range_with_commas(self):
        text = "1,5-2,5 года"
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 2)
        self.assertEqual([t.forms[0]['grammemes'] for t in tokens], [
            {'RANGE', 'FLOAT-RANGE'},
            {'inan', 'masc', 'sing', 'NOUN', 'gent'},
        ])

    def test_match_roman_number(self):
        text = 'XX век Fox'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertEqual([t.forms[0]['grammemes'] for t in tokens], [
            {'ROMN', 'NUMBER'},
            {'ADVB'},
            {'LATN'},
        ])
        self.assertEqual([t.value for t in tokens], [20, 'век', 'Fox'])

    def test_match_email_address(self):
        text = 'напиши на example@example.com'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertEqual([t.forms[0]['grammemes'] for t in tokens], [
            {'perf', 'tran', 'sing', 'excl', 'impr', 'VERB'},
            {'PREP'},
            {'EMAIL'},
        ])

    def test_match_phone_number(self):
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

    def test_match_unicode_digits(self):
        text = '٧ лет'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 2)
        self.assertEqual([t.value for t in tokens], [7, 'лет'])

    @unittest.skipIf(sys.version_info.major < 3, 'python 2 creates different objects for same xrange calls')
    @unittest.skipIf(platform.python_implementation() == 'PyPy', 'pypy & pypy3 have same semantics for range objects')
    def test_match_complex_ranges(self):
        text = 'А3-10-4,0-1.4301'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual([t.value for t in tokens[1:]], [range(3, 10), -4.0, -1.4301])

    def test_match_different_types_of_punctuation_characters(self):
        text = ':."'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 3)
        self.assertEqual([t.value for t in tokens], [':', '.', '"'])

    @unittest.skipIf(sys.version_info.major > 2, 'python3 correctly handles big ranges')
    def test_match_large_ranges(self):
        text = '1433 - 40817810505751201174'
        tokens = list(self.tokenizer.transform(text))
        self.assertEqual(len(tokens), 1)
        self.assertEqual(
            list(itertools.islice(tokens[0].value, 5)),
            [1433, 1434, 1435, 1436, 1437],
        )

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
                'normalization': NormalizationType.Inflected,
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

    @unittest.skipIf(platform.python_implementation() == 'PyPy', 'pypy fails this test case with no output')
    def test_get_normalized_text(self):
        grammar, tokens = next(
            self.parser.extract(
                self.person_text,
            )
        )
        original_text = get_normalized_text(tokens)
        self.assertEqual(original_text, 'иван иванов')

        grammar, tokens = next(
            self.parser.extract(
                'с василисой смирновой произошло невероятное ...',
            )
        )
        original_text = get_normalized_text(tokens)
        self.assertEqual(original_text, 'василиса смирнова')


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

        # TODO:
        # text = 'Саша была красивой, а её брат Саша был сильным'
        # results = parser.extract(text)
        # self.assertEqual([[w.value for w in n] for (_, n) in results], [['Саша', 'была'], ['Саша', 'был']])

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
        ])
        parser = Parser([
            grammar,
        ])
        results = parser.extract(text)
        self.assertEqual([[x.forms[0]['grammemes'] for x in tokens] for _, tokens in results], 
            [
                [
                    {'datv', 'anim', 'Ms-f', 'NOUN', 'Name', 'femn', 'sing'},
                    {'datv', 'anim', 'Surn', 'NOUN', 'masc', 'Sgtm', 'sing'},
                ],
                [
                    {'nomn', 'anim', 'Ms-f', 'NOUN', 'Name', 'femn', 'sing'},
                    {'nomn', 'anim', 'Surn', 'NOUN', 'Sgtm', 'femn', 'sing'},
                ],
                [
                    {'anim', 'Ms-f', 'NOUN', 'accs', 'Name', 'femn', 'sing'},
                    {'anim', 'Surn', 'NOUN', 'accs', 'Sgtm', 'femn', 'sing'},
                ],
                [
                    {'anim', 'Ms-f', 'NOUN', 'accs', 'Name', 'femn', 'sing'},
                    {'anim', 'masc', 'Surn', 'NOUN', 'accs', 'Sgtm', 'sing'},
                ],
            ]
        )

        text = 'иоганн вольфганг'
        grammar = Grammar('Latin_name', [
            {
                'labels': [
                    gram('Name'),
                ],
            },
            {
                'labels': [
                    gram('Name'),
                    gnc_match(-1, solve_disambiguation=True)
                ],
            },
        ])
        parser = Parser([
            grammar,
        ])
        results = list(parser.extract(text))
        self.assertEqual([[x.forms[0]['grammemes'] for x in tokens] for _, tokens in results], 
            [
                [
                    {'nomn', 'Name', 'NOUN', 'masc', 'sing', 'anim'},
                    {'nomn', 'Name', 'NOUN', 'masc', 'sing', 'anim'},
                ],
            ]
        )
        values = [[x.value for x in tokens] for _, tokens in results]
        self.assertEqual(values, [['иоганн', 'вольфганг']])

    def test_normalization_in_rules(self):
        text = 'в институте радионавигации и времени'
        grammar = Grammar('Educational', [
            {
                'labels': [
                    dictionary({
                        'институт',
                    }),
                ],
                'normalization': NormalizationType.Normalized,
            },
            {
                'labels': [
                    gram('gent'),
                ],
                'repeatable': True,
                'normalization': NormalizationType.Original,
            }
        ])
        parser = Parser([
            grammar,
        ])
        grammar, tokens = next(parser.extract(text))
        normalized = get_normalized_text(tokens)
        self.assertEqual(normalized, 'институт радионавигации и времени')

    def test_return_raw_stack(self):
        text = 'иван иванов'
        grammar = Grammar('Firstname_and_Lastname', [
            {
                'labels': [
                    gram('Name'),
                ],
            },
            {
                'labels': [
                    gram('Surn'),
                    gnc_match(-1, solve_disambiguation=True),
                ]
            },
        ])
        parser = Parser([grammar])
        g, tokens = next(parser.extract(text, return_flatten_stack=False))
        self.assertEqual(grammar, g)
        self.assertEqual([0, 1], [n for (n, _) in tokens])
        self.assertEqual(['иван', 'иванов'], [t.value for t in [t for (_, t) in tokens]])

    def test_operations_in_grammars(self):

        grammar = Grammar('House_Number', [
            OR([
                {
                    'labels': [
                        eq('кв'),
                    ],
                },
                {
                    'labels': [
                        gram('INT'),
                    ],
                },
            ],
            [
                {
                    'labels': [
                        eq('квартира'),
                    ],
                },
                {
                    'labels': [
                        gram('INT'),
                    ],
                },
            ])
        ])
        parser = Parser([grammar])
        text = 'кв 1'
        g, tokens = list(parser.extract(text))[0]
        self.assertEqual(g, grammar)
        self.assertEqual([t.value for t in tokens], ['кв', 1])

        text = 'квартира 1'
        g, tokens = list(parser.extract(text))[0]
        self.assertEqual(g, grammar)
        self.assertEqual([t.value for t in tokens], ['квартира', 1])

class DictionaryPipelineTestCase(unittest.TestCase):

    def test_match(self):
        text = 'иван приехал в нижний новгород'
        tokenizer = Tokenizer()
        tokens = tokenizer.transform(text)
        pipeline = DictionaryPipeline(dictionary={
            'нижний_новгород': [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}],
        })
        stream = pipeline(tokens)
        for token in stream:
            if token.value != 'нижний_новгород':
                continue
            else:
                self.assertEqual(token, Token(
                    'нижний_новгород',
                    (15, 30),
                    [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}]
                ))

    def test_match_in_different_form(self):
        text = 'в нижнем новгороде прошел ещё один день'
        tokenizer = Tokenizer()
        tokens = tokenizer.transform(text)
        pipeline = DictionaryPipeline(dictionary={
            'нижний_новгород': [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}],
        })
        stream = pipeline(tokens)
        for token in stream:
            if token.value != 'нижний_новгород':
                continue
            else:
                self.assertEqual(token, Token(
                    'нижнем_новгороде',
                    (2, 18),
                    [{'grammemes': ['Geox/City'], 'normal_form': 'нижний новгород'}]
                ))

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

        WithDescriptor = [
            {
                'labels': [
                    dictionary({
                        'представитель',
                    }),
                ]
            },
            {
                'labels': [
                    gram('accs'),
                    gram_not('Name'),
                ],
                'repeatable': True,
            },
            {
                'labels': [
                    gram('Name'),
                    gnc_match(0, solve_disambiguation=True),
                ],
            },
            {
                'labels': [
                    gram('Surn'),
                    gnc_match(0, solve_disambiguation=True),
                    gnc_match(-1, solve_disambiguation=True),
                ]
            }
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

    class Organisation(enum.Enum):

        Simple = [
            {
                'labels': [
                    dictionary({
                        'администрация',
                    }),
                ],
            },
            {
                'labels': [
                    gram('accs'),
                ],
                'repeatable': True,
            }
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

        text = 'представитель администрации президента иван иванов'
        combinator = Combinator([self.Person, self.Organisation])
        matches = list(combinator.extract(text))
        self.assertEqual(len(matches), 5)
        matches = list(combinator.resolve_matches(matches, strict=False))
        grammars = list(x[0] for x in matches)
        values = list([y.value for y in x[1]] for x in matches)
        self.assertEqual(grammars, [
            self.Person.WithDescriptor,
            self.Organisation.Simple,
        ])
        self.assertEqual(values, [['представитель', 'администрации', 'президента', 'иван', 'иванов'], ['администрации', 'президента']])

class InterpretationEngineTestCase(unittest.TestCase):

    def test_person_object_interpretation(self):

        class PersonInterpretation(InterpretationObject):

            class Attributes(enum.Enum):
                Firstname = 0 # иван
                Patrynomic = 1 # иванович
                Lastname = 2 # иванов
                Nickname = 3 # <иваныч>
                Descriptor = 4 # президент
                Description = 5 # российской федерации

            def __eq__(self, other):
                if isinstance(self.firstname, Token):
                    self_firstname = self.firstname.value
                else:
                    self_firstname = self.firstname

                if isinstance(other.firstname, Token):
                    other_firstname = other.firstname.value
                else:
                    other_firstname = other.firstname
                return self_firstname == other_firstname

        class Person(enum.Enum):

            FirstnameAndLastname = [
                {
                    'labels': [
                        gram('Name'),
                    ],
                    'normalization': NormalizationType.Inflected,
                    'interpretation': {
                        'attribute': PersonInterpretation.Attributes.Firstname,
                    }
                },
                {
                    'labels': [
                        gram('Surn'),
                        gnc_match(-1, solve_disambiguation=True),
                    ],
                    'normalization': NormalizationType.Inflected,
                    'interpretation': {
                        'attribute': PersonInterpretation.Attributes.Lastname,
                    }
                }
            ]

            LastnameAndFirstname = [
                {
                    'labels': [
                        gram('Surn'),
                    ],
                    'normalization': NormalizationType.Inflected,
                    'interpretation': {
                        'attribute': PersonInterpretation.Attributes.Lastname,
                    }
                },
                {
                    'labels': [
                        gram('Name'),
                        gnc_match(-1, solve_disambiguation=True),
                    ],
                    'normalization': NormalizationType.Inflected,
                    'interpretation': {
                        'attribute': PersonInterpretation.Attributes.Firstname,
                    }
                },
            ]

        text = 'иван иванов и иванова саша'
        combinator = Combinator([Person])
        matches = combinator.resolve_matches(
            combinator.extract(text)
        )
        engine = InterpretationEngine(object_class=PersonInterpretation)
        objects = list(engine.extract(matches))
        self.assertEqual(objects, [
            PersonInterpretation(**{
                'firstname': 'иван',
                'lastname': 'иванов',
            }),
            PersonInterpretation(**{
                'firstname': 'саша',
                'lastname': 'иванова',
            }),
        ])
        self.assertEqual(objects[0].firstname.value, 'иван')
        self.assertEqual(objects[0].lastname.value, 'иванов')
        self.assertEqual(objects[0].descriptor, None)

        self.assertEqual(objects[0].normalized, 'иван иванов')
        self.assertEqual(objects[1].normalized, 'иванова саша')

        self.assertEqual(
            objects[0].difference(
                objects[0],
            ),
            0,
        )

        self.assertEqual(
            objects[0].difference(
                objects[1],
            ),
            7,
        )
