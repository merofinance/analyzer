COLORS = {
    "green": "olivedrab",
    "blue": "cornflowerblue",
    "brown": "darkgoldenrod",
    "gray": "darkgray",
    "violet": "violet",
    "coral": "lightcoral",
    "teal": "teal",
}

DEFAULT_PALETTE = list(COLORS.values())


def make_palette(*colors):
    return [COLORS[c] for c in colors]
