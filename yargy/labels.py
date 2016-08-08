GENDERS = ("masc", "femn", "neut", "Ms-f")

def gram_label(token, value, stack):
    return value in token.grammemes

def gram_not_label(token, value, stack):
    return not value in token.grammemes

def gender_match_label(token, index, stack, genders=GENDERS):
    results = ((g in t.grammemes for g in genders) for t in (stack[index], token))

    *case_token_genders, case_token_msf = next(results)
    *candidate_token_genders, candidate_token_msf = next(results)

    if not candidate_token_genders == case_token_genders:
        if case_token_msf:
            if any(candidate_token_genders[:2]):
                return True
    else:
        return True
    return False

def dictionary_label(token, values, stack):
    return any((n in values) for n in token.forms)

LABELS_LOOKUP_MAP = {
    "gram": gram_label,
    "gram-not": gram_not_label,
    "dictionary": dictionary_label,
    "gender-match": gender_match_label,
}
