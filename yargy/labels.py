def gram_label(token, value, stack):
    return value in token.grammemes

LABELS_LOOKUP_MAP = {
    "gram": gram_label,
}
