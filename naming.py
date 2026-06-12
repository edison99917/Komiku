import re

_ILLEGAL = re.compile(r'[\\/:*?"<>|]')


def safe_filename(name):
    return _ILLEGAL.sub("", name).strip()


def chapter_label(number):
    if number == int(number):
        return str(int(number))
    return str(number)
