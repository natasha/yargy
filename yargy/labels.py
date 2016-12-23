# coding: utf-8
from __future__ import unicode_literals
from functools import wraps, partial

try:
    string_type = basestring
except NameError:
    string_type = str


GENDERS = ('masc', 'femn', 'neut', 'Ms-f', 'GNdr')
NUMBERS = ('sing', 'plur', 'Sgtm', 'Pltm')
CASES = ('nomn', 'gent', 'datv', 'accs', 'ablt', 'loct', 'voct', 'gen2', 'acc2', 'loc2', 'Fixd')

def get_token_features(candidate, case, grammemes):
    return ([g in t['grammemes'] for g in grammemes] for t in (case, candidate))

def string_required(func):
    @wraps(func)
    def wrapper(value, token, stack):
        if not isinstance(token.value, string_type):
            return False
        else:
            return func(value, token, stack)
    return wrapper

def label(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return partial(func, *args, **kwargs)
    return wrapper

@label
def and_(labels, token, stack):
    return all(
        label(token, stack) for label in labels
    )

@label
def or_(labels, token, stack):
    return any(
        label(token, stack) for label in labels
    )

@label
@string_required
def is_lower(value, token, stack):
    return token.value.islower() == value

@label
@string_required
def is_upper(value, token, stack):
    return token.value.isupper() == value

@label
@string_required
def is_title(value, token, stack):
    return token.value.istitle() == value

@label
@string_required
def is_capitalized(value, token, stack):
    '''
    http://bugs.python.org/issue7008
    '''
    return token.value[0].isupper() == value

@label
def eq(value, token, stack):
    return token.value == value

@label
def not_eq(value, token, stack):
    return token.value != value

@label
def in_(value, token, stack):
    return token.value in value

@label
def not_in(value, token, stack):
    return not token.value in value

@label
def gt(value, token, stack):
    return token.value > value

@label
def lt(value, token, stack):
    return token.value < value

@label
def gte(value, token, stack):
    return token.value >= value

@label
def lte(value, token, stack):
    return token.value <= value

@label
def is_instance(value, token, stack):
    return isinstance(token.value, value)

@label
def custom(function, token, stack):
    return function(token, stack)

@label
def gram(value, token, stack):
    for form in token.forms:
        if value in form['grammemes']:
            return True
    else:
        return False

@label
def gram_any(values, token, stack):
    return any(gram(value)(token, stack) for value in values)

@label
def gram_in(values, token, stack):
    return all(gram(value)(token, stack) for value in values)

@label
def gram_not(value, token, stack):
    return not gram(value)(token, stack)

@label
def gram_not_in(values, token, stack):
    return all(gram_not(value)(token, stack) for value in values)

def gender_match_check(candidate, case, genders=GENDERS):
    results = get_token_features(candidate, case, genders)

    case_token_results = next(results)
    case_token_msf, case_token_gndr = (
        case_token_results[-2],
        case_token_results[-1],
    )
    case_token_genders = case_token_results[:-2]

    candidate_token_results = next(results)
    candidate_token_msf, candidate_token_gndr = (
        candidate_token_results[-2],
        candidate_token_results[-1],
    )
    candidate_token_genders = candidate_token_results[:-2]

    if not candidate_token_genders == case_token_genders:
        if case_token_msf or candidate_token_msf:
            if any(case_token_genders[:2]) or any(candidate_token_genders[:2]):
                return True
        elif case_token_gndr or candidate_token_gndr:
            return True
        elif 'plur' in case['grammemes'] and 'plur' in candidate['grammemes']:
            return True
        else:
            if (case_token_genders[0] and candidate_token_genders[0]) or \
               (case_token_genders[1] and candidate_token_genders[1]) or \
               (case_token_genders[2] and candidate_token_genders[2]):
                return True
    else:
        return True

@label
def gender_match(index, token, stack):
    for candidate_form in token.forms:
        for case_form in stack[index].forms:
            match = gender_match_check(candidate_form, case_form)
            if match:
                return True
    return False

def number_match_check(candidate, case, numbers=NUMBERS):
    results = get_token_features(candidate, case, numbers)

    case_form_results = next(results)
    case_form_features, case_form_only_sing, case_form_only_plur = (
        case_form_results[:-2],
        case_form_results[-2],
        case_form_results[-1],
    )

    candidate_form_results = next(results)
    candidate_form_features, candidate_form_only_sing, candidate_form_only_plur = (
        candidate_form_results[:-2],
        candidate_form_results[-2],
        candidate_form_results[-1],
    )

    if case_form_features == candidate_form_features:
        return True
    elif case_form_only_sing or case_form_only_plur:
        if case_form_only_sing:
            if candidate_form_features[0]:
                return True
        elif case_form_only_plur:
            if candidate_form_features[1]:
                return True

@label
def number_match(index, token, stack):
    for candidate_form in token.forms:
        for case_form in stack[index].forms:
            match = number_match_check(candidate_form, case_form)
            if match:
                return True
    return False


def case_match_check(candidate, case, cases=CASES):
    results = get_token_features(candidate, case, cases)

    case_form_results = next(results)
    case_form_features, is_case_fixed = (
        case_form_results[:-1],
        case_form_results[-1],
    )

    candidate_form_results = next(results)
    candidate_form_features, is_candidate_fixed = (
        candidate_form_results[:-1],
        candidate_form_results[-1],
    )

    if case_form_features == candidate_form_features:
        return True
    elif is_case_fixed or is_candidate_fixed:
        return True

@label
def case_match(index, token, stack, cases=CASES):
    for candidate_form in token.forms:
        for case_form in stack[index].forms:
            match = case_match_check(candidate_form, case_form)
            if match:
                return True
    return False

@label
def gnc_match(index, token, stack, solve_disambiguation=False, match_all_disambiguation_forms=True):
    if solve_disambiguation:
        case_forms = []
        candidate_forms = []
    for candidate_form in token.forms:
        if not match_all_disambiguation_forms:
            if (case_forms and candidate_forms):
                break
        for case_form in stack[index].forms:
            match = all([
                gender_match_check(candidate_form, case_form),
                number_match_check(candidate_form, case_form),
                case_match_check(candidate_form, case_form),
            ])
            if match:
                if solve_disambiguation:
                    if not case_form in case_forms:
                        case_forms.append(case_form)
                    if not candidate_form in candidate_forms:
                        candidate_forms.append(candidate_form)
                    if not match_all_disambiguation_forms:
                        break
                else:
                    return True
    if solve_disambiguation and (case_forms and candidate_forms):
        token.forms = candidate_forms
        stack[index].forms = case_forms
        return True
    return False

@label
@string_required
def dictionary(values, token, stack):
    return any((form['normal_form'] in values) for form in token.forms)

@label
@string_required
def dictionary_not(values, token, stack):
    return not dictionary(values)(token, stack)
