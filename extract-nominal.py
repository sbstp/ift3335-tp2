from pathlib import Path
import re

RE_SEPARATOR = re.compile(r"[\n\t\s\[\]]+")
N_WORDS = 4
STOP_WORDS = set(word.strip() for word in Path('stoplist-english.txt').read_text().split("\n") if word.strip())


class Word:

    def __init__(self, text, cat):
        self.text = text
        self.cat = cat

    def __repr__(self):
        return "{}/{}".format(self.text, self.cat)


class Entry:

    def __init__(self, meaning, words=None):
        self.meaning = meaning
        self.words = words or []

    def __repr__(self):
        return "Entry({}, {!r})".format(self.meaning, self.words)


def escape(s):
    return s.replace("'", "\\'")


def printf(fmt, *args, **kwargs):
    print(fmt.format(*args, **kwargs))


def format_iterable(items):
    pieces = []
    for item in items:
        if item is None:
            pieces.append('?')
        elif isinstance(item, str):
            pieces.append("'" + escape(item) + "'")
        elif isinstance(item, int):
            pieces.append(str(item))
    return ','.join(pieces)


def print_row(*cells):
    print(format_iterable(cells))


def get(list, index, default=None):
    try:
        return list[index]
    except IndexError:
        return None


def find_context(words, pos, prev=False, n=N_WORDS/2):
    """
    Find the n previous/next non stop words in the list of words.
    If we run out of bounds in the list of words, None is used.
    """
    direction = -1 if prev else 1
    selection = []
    while n > 0:
        pos += direction
        sel = get(words, pos)
        if sel is None:
            n -= 1
            selection.append(None)
        elif sel.text not in STOP_WORDS:
            selection.append(sel)
            n -= 1
    return selection


raw_data = Path("interest.acl94.txt").read_text()
samples = [sample.strip() for sample in raw_data.split("$$")]
entries = []

for sample in samples:
    words = [Word(*wordcat.split("/"))
             for wordcat in RE_SEPARATOR.split(sample)
             if "/" in wordcat]
    if not words:
        continue
    pos = None
    meaning = None
    for (idx, word) in enumerate(words):
        if word.text.startswith("interest_") or word.text.startswith("interests_"):
            pos = idx
            meaning = int(word.text.split('_')[1])
            break

    # e = Entry(meaning, [get(words, pos - 2), get(words, pos - 1), get(words, pos + 1), get(words, pos + 2)])
    e = Entry(meaning, find_context(words, pos, prev=True) + find_context(words, pos))
    assert len(e.words) == N_WORDS
    entries.append(e)

nominal_word_sets = [set() for _ in range(N_WORDS)]
nominal_cat_sets = [set() for _ in range(N_WORDS)]

for entry in entries:
    for idx, word in enumerate(entry.words):
        if word is not None:
            nominal_word_sets[idx].add(word.text)
            nominal_cat_sets[idx].add(word.cat)

printf("@relation interest")
printf("")

printf("@attribute meaning {{1,2,3,4,5,6}}")

for i in range(N_WORDS):
    printf("@attribute word{} {{{}}}", i, format_iterable(nominal_word_sets[i]))
    printf("@attribute cat{} {{{}}}", i, format_iterable(nominal_cat_sets[i]))

printf("")
printf("@data")
for entry in entries:
    row = [entry.meaning]
    for word in entry.words:
        if word is not None:
            row.append(word.text)
            row.append(word.cat)
        else:
            row.append(None)
            row.append(None)
    print_row(*row)
