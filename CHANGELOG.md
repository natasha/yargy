## 0.10 (dev)
* Refactor tokenizer
* Inline pipelines
* Lazy predicates
* Refactor interpretation
* Reimplement rule relations 

See https://github.com/natasha/yargy/pull/48 for more

## 0.9
Major update required to support recursive grammar.
* Library API changed including grammar DSL and parser API
* Components updated: tokenizer, pipelines, parser, interpretation

## 0.6.0
* Initial object interpretation support
* Replaced custom tree-like struct used in `combinator.resolve_matches` method with `IntervalTree`
* `number_match` and `case_match` labels now have understand same arguments as `gnc_match` label

## 0.5.1 - 0.5.3
* Support `match_all_disambiguation_forms` argument in `gnc_match` label
* New token types - `ROMN` for roman numbers, like `XXI`, `EMAIL` for emails and `PHONE` for phone numbers
* New labels - `and_` & `or_`
* Implemented `get_normalized_text` function that returns normalized text from parsed tokens

## 0.5.0
* Partial morphology disambiguation solving support (`gnc_match` label now accepts optional boolean argument `solve_disambiguation`, which when is True, reduces number of token forms in result match)
* Rewrited labels, now they're function-based
* Rewrited tokenizer's `transform` function for better extending
* Tokenizer now adds different types of grammemes for different types of quotes (e.g. `L-QUOTE` for `«` quote)
* Implemented DAWG-based pipeline, which shows better performance over dictionary-based pipeline

## 0.4.1 - 0.4.6
* Reimplemented `resolve_matches` method in `Combinator`
* [fix] Fixed error at parsing float range with comma as delimiter
* [fix] Additional checks for terminal rule at `reduce` grammars method
* [fix] Fixed requirements in setup.py
* [fix] Tokenizer now correctly understands range values on Python2.x and PyPy platforms
* [fix] Create new grammars with terminal rule instead of appending it to original one

## 0.4
* Replaced shift-reduce parser with GLR parser, because it provides much more performance on multiple grammars (linear time with GLR vs. exponental time with shift-reduce parser).
* Pipelines support
* Added support for Python 2.7 & PyPy

## 0.3
* Implemented `gnc-match`, `in` labels

## 0.2
* Implemented `gender-match`, `number-match`, `case-match` labels
* Replace `is-title` label with `is-capitalized` label, due to http://bugs.python.org/issue7008
* Tokenizer now understands integer and float ranges (actually, two numbers separated by dash)

## 0.1
* Initial release
