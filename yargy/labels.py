def gram_label(token, value, stack):
    return value in token.grammemes

def gram_not_label(token, value, stack):
    return not value in token.grammemes

LABELS_LOOKUP_MAP = {
    "gram": gram_label,
    "gram-not": gram_not_label,
}
