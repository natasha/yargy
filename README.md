# Yargy [![Build Status](https://travis-ci.org/natasha/yargy.svg?branch=master)](https://travis-ci.org/natasha/yargy) [![Build status](https://ci.appveyor.com/api/projects/status/ik1tf9n32yh9wfy5?svg=true)](https://ci.appveyor.com/project/dveselov/yargy) [![Documentation Status](https://readthedocs.org/projects/yargy/badge/?version=latest)](http://yargy.readthedocs.io/) [![PyPI](https://img.shields.io/pypi/v/yargy.svg)](https://pypi.python.org/pypi/yargy)

`Yargy` is a Earley parser, that uses russian morphology for facts extraction process, and written in pure python

# Install

`Yargy` supports both Python 2.7+ / 3.3+ versions including PyPy.

```bash
$ pip install yargy
```

# Usage

```python
from yargy import Parser, rule, and_, not_
from yargy.interpretation import fact
from yargy.predicates import gram
from yargy.relations import gnc_relation
from yargy.pipelines import morph_pipeline


Name = fact(
    'Name',
    ['first', 'last'],
)
Person = fact(
    'Person',
    ['position', 'name']
)

LAST = and_(
    gram('Surn'),
    not_(gram('Abbr')),
)
FIRST = and_(
    gram('Name'),
    not_(gram('Abbr')),
)

POSITION = morph_pipeline([
    'управляющий директор',
    'вице-мэр'
])

gnc = gnc_relation()
NAME = rule(
    FIRST.interpretation(
        Name.first
    ).match(gnc),
    LAST.interpretation(
        Name.last
    ).match(gnc)
).interpretation(
    Name
)

PERSON = rule(
    POSITION.interpretation(
        Person.position
    ).match(gnc),
    NAME.interpretation(
        Person.name
    )
).interpretation(
    Person
)

parser = Parser(PERSON)

match = parser.match('управляющий директор Иван Ульянов')
print(match)

```

And in output you will see something like this:
```python
Person(
    position='управляющий директор',
    name=Name(
        first='Иван',
        last='Ульянов'
)
```

For more examples, details on grammar syntax, predicates and pipelines see [Yargy documentation](http://yargy.readthedocs.io/ru/latest/).

# License

Source code of `yargy` is distributed under MIT license (allows modification and commercial usage)

# Support

- Chat — https://telegram.me/natural_language_processing
- Issues — https://github.com/natasha/yargy/issues
- Commercial support — http://lab.alexkuk.ru/natasha
