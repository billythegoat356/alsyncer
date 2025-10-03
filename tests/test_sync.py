from alsyncer import sync_alignment, CharAlignment



def T(
        altext,
        aldurs,
        rtext,
        expected_durs
):
    alignment = [
        CharAlignment(character=char, duration=dur)
        for char, dur in zip(altext, aldurs)
    ]
    sync_alignment(alignment, rtext)

    assert ''.join(al.character for al in alignment) == rtext # Text respected
    assert sum(al.duration for al in alignment) == sum(aldurs) # Durations conserved
    assert [al.duration for al in alignment] == [*expected_durs] # Durs like expected


def test_1():
    T(
        "Hi",
        (100, 50),
        "Hi!",
        (100, 25, 25)
    )


def test_2():
    T(
        "Hi!",
        (100, 25, 25),
        "Hi",
        (100, 50)
    )

def test_3():
    T(
        "Hello",
        (100, 50, 50, 50, 50),
        "Hel",
        (100, 50, 150)
    )


def test_4():
    T(
        "Hel",
        (100, 50, 150),
        "Hello",
        (100, 50, 50, 50, 50)
    )


def test_5():
    # Insert a leading character. Expect the duration to be split evenly
    # from the first original character ("H": 100 -> "!" 50, "H" 50).
    # The rest stays the same.
    T(
        "Hi",
        (100, 50),
        "!Hi",
        (50, 50, 50)
    )
