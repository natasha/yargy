GENDERS = ("masc", "femn", "neut", "Ms-f", "GNdr")
NUMBERS = ("sing", "plur")

def get_token_features(candidate, case, grammemes):
    return ((g in t[3]["grammemes"] for g in grammemes) for t in (case, candidate))

def is_lower_label(token, _, stack):
    return token[1].islower()

def is_upper_label(token, _, stack):
    return token[1].isupper()

def is_title_label(token, _, stack):
    return token[1].istitle()

def is_capitalized_label(token, _, stack):
    """
    http://bugs.python.org/issue7008
    """
    return token[1][0].isupper() and token[1][-1].islower()

def eq_label(token, value, stack):
    return token[1] == value

def gt_label(token, value, stack):
    return token[1] > value

def lt_label(token, value, stack):
    return token[1] < value

def gte_label(token, value, stack):
    return token[1] >= value

def lte_label(token, value, stack):
    return token[1] <= value

def gram_label(token, value, stack):
    return value in token[3]["grammemes"]

def gram_any_label(token, values, stack):
    return any(gram_label(token, value, stack) for value in values)

def gram_in_label(token, values, stack):
    return all(gram_label(token, value, stack) for value in values)

def gram_not_label(token, value, stack):
    return not value in token[3]["grammemes"]

def gram_not_in_label(token, values, stack):
    return all(gram_not_label(token, value, stack) for value in values)

def gender_match_label(token, index, stack, genders=GENDERS):
    results = get_token_features(token, stack[index], genders)

    *case_token_genders, case_token_msf, case_token_gndr = next(results)
    *candidate_token_genders, candidate_token_msf, candidate_token_gndr = next(results)

    if not candidate_token_genders == case_token_genders:
        if case_token_msf or candidate_token_msf:
            if any(case_token_genders[:2]) or any(candidate_token_genders[:2]):
                return True
        elif case_token_gndr or candidate_token_gndr:
            return True
        elif "plur" in stack[index][3]["grammemes"] and "plur" in token[3]["grammemes"]:
            return True
        else:
            if (case_token_genders[0] and candidate_token_genders[0]) or \
               (case_token_genders[1] and candidate_token_genders[1]) or \
               (case_token_genders[2] and candidate_token_genders[2]):
               return True
    else:
        return True
    return False

def dictionary_label(token, values, stack):
    return any((n in values) for n in token[3]["forms"])

LABELS_LOOKUP_MAP = {
    "gram": gram_label,
    "gram-any": gram_any_label,
    "gram-in": gram_in_label,
    "gram-not": gram_not_label,
    "gram-not-in": gram_not_in_label,

    "gender-match": gender_match_label,

    "is-lower": is_lower_label,
    "is-upper": is_upper_label,
    "is-title": is_title_label,
    "is-capitalized": is_capitalized_label,

    "eq": eq_label,
    "gt": gt_label,
    "lt": lt_label,
    "gte": gte_label,
    "lte": lte_label,
    "dictionary": dictionary_label,
}
