# yargy [![Build Status](https://travis-ci.org/bureaucratic-labs/yargy.svg?branch=master)](https://travis-ci.org/bureaucratic-labs/yargy)

```python
from yargy import FactParser

text = "газета «Коммерсантъ» сообщила ..."
rules = (("word", {}), ("quote", {}), ("word", {}), ("quote", {}), ("$", {}))
parser = FactParser(rules)

for result in parser.parse(text):
    print(result)

"""
Will print:
[
    ('word', 'газета', (0, 6), {'grammemes': {'nomn', 'NOUN', 'sing', 'femn', 'inan'}, 'forms': {'газета'}}),
    ('quote', '«', (7, 8), None),
    ('word', 'Коммерсантъ', (8, 19), {'grammemes': {'Fixd', 'loct', 'anim', 'accs', 'gent', 'NOUN', 'ablt', 'plur', 'masc', 'datv', 'sing', 'nomn'}, 'forms': {'коммерсантъ'}}),
    ('quote', '»', (19, 20), None)
]
"""
```

```python

text = open("leo-tolstoy-war-and-peace.txt").read()

rules = (("word", {"labels": [
            ("gram", "Name"),
        ]}), 
         ("word", {"labels": [
            ("gram", "VERB"),
            ("gender-match", 0), # labels index is rule-based, 
                                 # so this VERB will be
                                 # compared with word
                                 # that matches rules[0]
        ]}), 
         ("$", {})
)

parser = FactParser(rules)

for line in text.splitlines():
    for result in parser.parse(line):
        print(result)

"""
Will print:
[
    ('word', 'Василий', (292, 299), {'grammemes': {'nomn', 'Name', 'masc', 'anim', 'NOUN', 'sing'}, 'forms': {'василий'}}), 
    ('word', 'говорил', (300, 307), {'grammemes': {'impf', 'tran', 'masc', 'indc', 'past', 'VERB', 'sing'}, 'forms': {'говорить'}})
]
[
    ('word', 'Пьер', (771, 775), {'grammemes': {'nomn', 'Name', 'masc', 'anim', 'NOUN', 'sing'}, 'forms': {'пьер'}}),
    ('word', 'был', (776, 779), {'grammemes': {'intr', 'impf', 'masc', 'indc', 'past', 'VERB', 'sing'}, 'forms': {'быть'}})
]
[
    ('word', 'Элен', (40, 44), {'grammemes': {'Name', 'Fixd', 'Sgtm', 'loct', 'anim', 'accs', 'NOUN', 'gent', 'ablt', 'femn', 'plur', 'datv', 'sing', 'nomn'}, 'forms': {'элен', 'элена'}}),
    ('word', 'сказала', (49, 56), {'grammemes': {'tran', 'indc', 'past', 'VERB', 'sing', 'perf', 'femn'}, 'forms': {'сказать'}})]
[
    ('word', 'Ипполит', (6, 13), {'grammemes': {'nomn', 'Name', 'masc', 'anim', 'NOUN', 'sing'}, 'forms': {'ипполит'}}),
    ('word', 'перенес', (14, 21), {'grammemes': {'tran', 'masc', 'indc', 'past', 'VERB', 'sing', 'perf'}, 'forms': {'перенести'}})
]
"""
```

# Internals

`yargy` parses russian text into AST, adds morphology information to `word` tags, then compares AST to given rules.
