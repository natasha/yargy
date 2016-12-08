# coding: utf-8
from __future__ import unicode_literals
from functools import wraps

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
    def wrapper(token, value, stack):
        if not isinstance(token.value, string_type):
            return False
        else:
            return func(token, value, stack)
    return wrapper

@string_required
def is_lower_label(token, value, stack):
    return token.value.islower() == value

@string_required
def is_upper_label(token, value, stack):
    return token.value.isupper() == value

@string_required
def is_title_label(token, value, stack):
    return token.value.istitle() == value

@string_required
def is_capitalized_label(token, value, stack):
    '''
    http://bugs.python.org/issue7008
    '''
    return token.value[0].isupper() == value

def eq_label(token, value, stack):
    return token.value == value

def not_eq_label(token, value, stack):
    return token.value != value

def in_label(token, value, stack):
    return token.value in value

def not_in_label(token, value, stack):
    return not token.value in value

def gt_label(token, value, stack):
    return token.value > value

def lt_label(token, value, stack):
    return token.value < value

def gte_label(token, value, stack):
    return token.value >= value

def lte_label(token, value, stack):
    return token.value <= value

def is_instance_label(token, value, stack):
    return isinstance(token.value, value)

def custom_label(token, function, stack):
    return function(token, stack)

def gram_label(token, value, stack):
    for form in token.forms:
        if value in form['grammemes']:
            return True
    return False

def gram_any_label(token, values, stack):
    return any(gram_label(token, value, stack) for value in values)

def gram_in_label(token, values, stack):
    return all(gram_label(token, value, stack) for value in values)

def gram_not_label(token, value, stack):
    return not gram_label(token, value, stack)

def gram_not_in_label(token, values, stack):
    return all(gram_not_label(token, value, stack) for value in values)

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

def gender_match_label(token, index, stack):
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

def number_match_label(token, index, stack):
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

def case_match_label(token, index, stack, cases=CASES):
    for candidate_form in token.forms:
        for case_form in stack[index].forms:
            match = case_match_check(candidate_form, case_form)
            if match:
                return True
    return False

def gnc_match_label(token, index, stack):
    for candidate_form in token.forms:
        for case_form in stack[index].forms:
            match = all([
                gender_match_check(candidate_form, case_form),
                number_match_check(candidate_form, case_form),
                case_match_check(candidate_form, case_form),
            ])
            if match:
                return True
    return False

@string_required
def dictionary_label(token, values, stack):
    return any((form['normal_form'] in values) for form in token.forms)

@string_required
def dictionary_not_label(token, values, stack):
    return not dictionary_label(token, values, stack)

LABELS_LOOKUP_MAP = {
    'gram': gram_label,
    'gram-any': gram_any_label,
    'gram-in': gram_in_label,
    'gram-not': gram_not_label,
    'gram-not-in': gram_not_in_label,
    'dictionary': dictionary_label,
    'dictionary-not': dictionary_not_label,

    'gender-match': gender_match_label,
    'number-match': number_match_label,
    'case-match': case_match_label,
    'gnc-match': gnc_match_label,

    'is-lower': is_lower_label,
    'is-upper': is_upper_label,
    'is-title': is_title_label,
    'is-capitalized': is_capitalized_label,

    'eq': eq_label,
    'not-eq': not_eq_label,
    'in': in_label,
    'not-in': not_in_label,
    'gt': gt_label,
    'lt': lt_label,
    'gte': gte_label,
    'lte': lte_label,
    'is-instance': is_instance_label,
    'custom': custom_label,
}
