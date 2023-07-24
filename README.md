<img src="https://github.com/natasha/natasha-logos/blob/master/yargy.svg">

![CI](https://github.com/natasha/yargy/actions/workflows/test.yml/badge.svg)

Yargy uses rules and dictionaries to extract structured information from Russian texts. Yargy is similar to <a href="https://yandex.ru/dev/tomita">Tomita parser</a>.

## Install

Yargy supports Python 3.7+, PyPy 3, depends only on <a href="http://github.com/pymorphy2/pymorphy2">Pymorphy2</a>.

```bash
$ pip install yargy
```

## Usage

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

Person(
    position='управляющий директор',
    name=Name(
        first='Иван',
        last='Ульянов'
    )
)

```

## Documentation

All materials are in Russian:

* <a href="https://habr.com/ru/post/349864/">Overview</a>
* <a href="https://www.youtube.com/watch?v=NQxzx0qYgK8">Video from workshop</a>
* <a href="https://nbviewer.jupyter.org/github/natasha/yargy/blob/master/docs/index.ipynb">Getting started</a>
* <a href="https://nbviewer.jupyter.org/github/natasha/yargy/blob/master/docs/ref.ipynb">Reference</a>
* <a href="https://nbviewer.jupyter.org/github/natasha/yargy/blob/master/docs/cookbook.ipynb">Cookbook</a>
* <a href="https://github.com/natasha/yargy-examples">Examples</a>
* <a href="https://github.com/natasha/natasha-usage#yargy">Code snippets</a>

## Support

- Chat — https://t.me/natural_language_processing
- Issues — https://github.com/natasha/yargy/issues
- Commercial support — https://lab.alexkuk.ru

## Development

Dev env

```bash
brew install graphviz

python -m venv ~/.venvs/natasha-yargy
source ~/.venvs/natasha-yargy/bin/activate

pip install -r requirements/dev.txt
pip install -e .

python -m ipykernel install --user --name natasha-yargy
```

Test + lint

```bash
make test
```

Update docs

```bash
make exec-docs

# Manually check git diff docs/, commit
```

Release

```bash
# Update setup.py version

git commit -am 'Up version'
git tag v0.16.0

git push
git push --tags

# Github Action builds dist and publishes to PyPi
```
