GENDERS = ('masc', 'femn', 'neut', 'Ms-f', 'GNdr')
NUMBERS = ('sing', 'plur', 'Pltm')
CASES = ('nomn', 'gent', 'datv', 'accs', 'ablt', 'loct', 'voct', 'gen2', 'acc2', 'loc2', 'Fixd')

def get_token_features(candidate, case, grammemes):
    return ((g in t['grammemes'] for g in grammemes) for t in (case, candidate))

def is_lower_label(token, _, stack):
    return token.value.islower()

def is_upper_label(token, _, stack):
    return token.value.isupper()

def is_title_label(token, _, stack):
    return token.value.istitle()

def is_capitalized_label(token, _, stack):
    '''
    http://bugs.python.org/issue7008
    '''
    return token.value[0].isupper() and token.value[-1].islower()

def eq_label(token, value, stack):
    return token.value == value

def not_eq_label(token, value, stack):
    return token.value != value

def in_label(token, value, stack):
    return token.value in value

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

def gender_match_label(token, index, stack, genders=GENDERS):
    for candidate_form in token.forms:
        for case_form in stack[index].forms:
            results = get_token_features(candidate_form, case_form, genders)

            *case_token_genders, case_token_msf, case_token_gndr = next(results)
            *candidate_token_genders, candidate_token_msf, candidate_token_gndr = next(results)

            if not candidate_token_genders == case_token_genders:
                if case_token_msf or candidate_token_msf:
                    if any(case_token_genders[:2]) or any(candidate_token_genders[:2]):
                        return True
                elif case_token_gndr or candidate_token_gndr:
                    return True
                elif 'plur' in case_form['grammemes'] and 'plur' in candidate_form['grammemes']:
                    return True
                else:
                    if (case_token_genders[0] and candidate_token_genders[0]) or \
                       (case_token_genders[1] and candidate_token_genders[1]) or \
                       (case_token_genders[2] and candidate_token_genders[2]):
                       return True
            else:
                return True
    return False

def number_match_label(token, index, stack, numbers=NUMBERS):
    for candidate_form in token.forms:
        for case_form in stack[index].forms:
            results = get_token_features(candidate_form, case_form, numbers)
            *case_form_features, case_form_only_plur = next(results)
            *candidate_form_features, candidate_form_only_plur = next(results)
            if case_form_features == candidate_form_features:
                return True
            elif case_form_only_plur or candidate_form_only_plur:
                if case_form_only_plur:
                    if candidate_form_features[1]:
                        return True
                else:
                    if case_form_features[1]:
                        return True
    return False

def case_match_label(token, index, stack, cases=CASES):
    for candidate_form in token.forms:
        for case_form in stack[index].forms:
            results = get_token_features(candidate_form, case_form, cases)
            *case_form_features, is_case_fixed = next(results)
            *candidate_form_features, is_candidate_fixed = next(results)
            if case_form_features == candidate_form_features:
                return True
            elif is_case_fixed or is_candidate_fixed:
                return True
    return False

def gnc_match_label(token, index, stack):
    return all([
        gender_match_label(token, index, stack),
        number_match_label(token, index, stack),
        case_match_label(token, index, stack),
    ])

def dictionary_label(token, values, stack):
    return any((form['normal_form'] in values) for form in token.forms)

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
    'gt': gt_label,
    'lt': lt_label,
    'gte': gte_label,
    'lte': lte_label,
    'is-instance': is_instance_label,
    'custom': custom_label,
}
