from alsyncer.syncer import add_missing
from alsyncer.models import CharAlignment

from rich import print


# --- Helpers -----------------------------------------------------------------

def AL(chars, durs):
    """Build an alignment list from parallel sequences of characters and durations."""
    assert len(chars) == len(durs)
    return [CharAlignment(character=c, duration=d) for c, d in zip(chars, durs)]

def chars_of(al):
    return [x.character for x in al]

def durs_of(al):
    return [x.duration for x in al]



def test_kA():
    al = add_missing(
        AL("A", [100]),
        "kA",
        missing=[0]
    )
    assert durs_of(al) == [50, 50]
    assert ''.join(chars_of(al)) == "kA"

def test_Ak():
    al = add_missing(
        AL("A", [100]),
        "Ak",
        missing=[1]
    )
    assert durs_of(al) == [50, 50]
    assert ''.join(chars_of(al)) == "Ak"


def test_Akk():
    al = add_missing(
        AL("A", [100]),
        "Akk",
        missing=[1, 2]
    )
    assert durs_of(al) == [100/3, 100/3, 100/3]
    assert ''.join(chars_of(al)) == "Akk"



def test_kkA():
    al = add_missing(
        AL("A", [100]),
        "kkA",
        missing=[0, 1]
    )
    assert durs_of(al) == [100/3, 100/3, 100/3]
    assert ''.join(chars_of(al)) == "kkA"


def test_AkB():
    al = add_missing(
        AL("AB", [60, 60]),
        "AkB",
        missing=[1]
    )
    assert durs_of(al) == [40, 40, 40]
    assert ''.join(chars_of(al)) == "AkB"


def test_AkkB():
    al = add_missing(
        AL("AB", [60, 60]),
        "AkkB",
        missing=[1, 2]
    )
    assert durs_of(al) == [30] * 4
    assert ''.join(chars_of(al)) == "AkkB"

def test_AkkkB():
    al = add_missing(
        AL("AB", [75, 75]),
        "AkkkB",
        missing=[1, 2, 3]
    )
    assert durs_of(al) == [30, 30, 30, 30, 30]
    assert ''.join(chars_of(al)) == "AkkkB"

def test_AkkkkB():
    al = add_missing(
        AL("AB", [150, 150]),
        "AkkkkB",
        missing=[1, 2, 3, 4]
    )
    assert durs_of(al) == [50] * 6
    assert ''.join(chars_of(al)) == "AkkkkB"



def test_kAkB():
    al = add_missing(
        AL("AB", [125, 75]),
        "kAkB",
        missing=[0, 2]
    )
    assert durs_of(al) == [50, 50, 50, 50]
    assert ''.join(chars_of(al)) == "kAkB"


def test_AkBk():
    al = add_missing(
        AL("AB", [75, 125]),
        "AkBk",
        missing=[1, 3]
    )
    assert durs_of(al) == [50, 50, 50, 50]
    assert ''.join(chars_of(al)) == "AkBk"


def test_kkAkB():
    al = add_missing(
        AL("AB", [175, 75]),
        "kkAkB",
        missing=[0, 1, 3]
    )
    assert durs_of(al) == [50, 50, 50, 50, 50]
    assert ''.join(chars_of(al)) == "kkAkB"


def test_AkBkk():
    al = add_missing(
        AL("AB", [75, 175]),
        "AkBkk",
        missing=[1, 3, 4]
    )
    assert durs_of(al) == [50, 50, 50, 50, 50]
    assert ''.join(chars_of(al)) == "AkBkk"



def test_kkAkkB():
    al = add_missing(
        AL("AB", [200, 100]),
        "kkAkkB",
        missing=[0, 1, 3, 4]
    )
    assert durs_of(al) == [50, 50, 50, 50, 50, 50]
    assert ''.join(chars_of(al)) == "kkAkkB"

def test_AkkBkk():
    al = add_missing(
        AL("AB", [100, 200]),
        "AkkBkk",
        missing=[1, 2, 4, 5]
    )
    assert durs_of(al) == [50, 50, 50, 50, 50, 50]
    assert ''.join(chars_of(al)) == "AkkBkk"

