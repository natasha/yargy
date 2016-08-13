GENDERS = ("masc", "femn", "neut", "Ms-f", "GNdr")

def get_token_features(candidate, case, grammemes):
    return ((g in t[3]["grammemes"] for g in grammemes) for t in (case, candidate))

def gram_label(token, value, stack):
    return value in token[3]["grammemes"]

def gram_not_label(token, value, stack):
    return not value in token[3]["grammemes"]

def gender_match_label(token, index, stack, genders=GENDERS):
    results = get_token_features(token, stack[index], genders)

    *case_token_genders, case_token_msf, case_token_gndr = next(results)
    *candidate_token_genders, candidate_token_msf, candidate_token_gndr = next(results)

    if not candidate_token_genders == case_token_genders:
        if case_token_msf:
            if any(candidate_token_genders[:2]):
                return True
        elif case_token_gndr or candidate_token_gndr:
            return True
    elif all(("plur" in stack[index].grammemes, "plur" in token.grammemes)):
        return True
    else:
        return True
    return False

def dictionary_label(token, values, stack):
    return any((n in values) for n in token[3]["forms"])

LABELS_LOOKUP_MAP = {
    "gram": gram_label,
    "gram-not": gram_not_label,
    "dictionary": dictionary_label,
    "gender-match": gender_match_label,
}
