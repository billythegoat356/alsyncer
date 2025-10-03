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

def test_6():
    # Insert 1 char between 'e' (60) and 'l' (30), distribute symmetrically:
    # New 'e' = 2/3*60 = 40
    # New 'l' = 2/3*30 = 20
    # Inserted '!' = 1/3*60 + 1/3*30 = 20 + 10 = 30
    # 'H' is unchanged.
    T(
        "Hel",
        (100, 60, 30),
        "He!l",
        (100, 40, 30, 20)
    )

def test_7():
    # Insert 2 chars between 'e' (60) and 'o' (40); symmetric distribution:
    # For n=2 inserts, each neighbor keeps 2/4 of its duration.
    # e': 2/4*60 = 30
    # o': 2/4*40 = 20
    # l1 (closer to e): 2/4*60 = 30
    # l2 (closer to o): 2/4*40 = 20
    # 'H' unchanged.
    T(
        "Heo",
        (100, 60, 40),
        "Hello",
        (100, 30, 30, 20, 20)
    )


def test_8():
    # Remove 2 additions in the middle ("Hel!!lo" -> "Hello").
    # Per README: for two consecutive additions between A and B,
    # the leftmost goes to A, the rightmost goes to B (no averaging).
    #
    # Before: H(100) e(40) l1(30) !(10) !(20) l2(25) o(35)
    # After:  H(100) e(40) l1(30+10=40) l2(25+20=45) o(35)
    T(
        "Hel!!lo",
        (100, 40, 30, 10, 20, 25, 35),
        "Hello",
        (100, 40, 40, 45, 35)
    )


def test_9():
    # Remove 3 additions between two neighbors (odd count ⇒ middle splits evenly).
    # Input:  "Hel!!!lo"  →  Output: "Hello"
    # Durations before: H(100) e(40) l1(30) !a(10) !b(20) !c(30) l2(25) o(35)
    # Rule per README (Additions removal):
    # - Leftmost addition goes entirely to the left neighbor (l1): +10
    # - Rightmost addition goes entirely to the right neighbor (l2): +30
    # - Middle addition (20) is split evenly between both neighbors: +10 each
    # After:
    #   l1': 30 + 10 (leftmost) + 10 (half of middle) = 50
    #   l2': 25 + 30 (rightmost) + 10 (half of middle) = 65
    # Others unchanged.
    T(
        "Hel!!!lo",
        (100, 40, 30, 10, 20, 30, 25, 35),
        "Hello",
        (100, 40, 50, 65, 35)
    )

def test_10():
    # Mixed case: remove an addition in the middle, then insert a missing char.
    #
    # Alignment → Reference:  "H!lo"  →  "Hello"
    # Durations before: H(90)  !(30)  l(30)  o(50)
    #
    # Step 1 — Additions removal (one '!' between H and l):
    #   Single middle addition splits evenly to both neighbors:
    #     H: 90 + 30/2 = 105
    #     l: 30 + 30/2 = 45
    #     o unchanged: 50
    #
    # Step 2 — Missing char insertion (insert 'e' between H and l, n=1):
    #   Symmetric distribution for 1 insert:
    #     H keeps 2/3 of 105 → 70
    #     l keeps 2/3 of 45  → 30
    #     inserted 'e' gets 1/3 of each neighbor → 105/3 + 45/3 = 35 + 15 = 50
    #
    # Expected after sync:
    #   "Hello" with durations: H(70), e(50), l(30), l(unchanged second l? none here), o(50)
    T(
        "H!lo",
        (90, 30, 30, 50),
        "Hello",
        (52, 53, 22, 23, 50)
    )


def test_11():
    # Complex mixed case: additions on left/center/right, and missings in center and at the end.
    #
    # Alignment → Reference:
    #   "?He!lo??"  →  "Hello!"
    #
    # Durations before:
    #   ?(12) H(80) e(60) !(30) l(40) o(70) ?(15) ?(25)
    #
    # Step A — Remove additions (per README rules):
    #   - Leading '?' at far left → all to nearest neighbor H: H=80+12=92
    #   - Single '!' between e and l (odd count) → split evenly to both:
    #       e=60+15=75, l=40+15=55
    #   - Trailing '??' at far right → both to nearest neighbor o:
    #       o=70+15+25=110
    #   Now: "H e l o" with (92, 75, 55, 110); total conserved = 332
    #
    # Step B — Insert missings:
    #   1) Missing 'l' between e(75) and l(55), n=1 (symmetric):
    #        e' = 2/3*75 = 50
    #        new_l = 1/3*75 + 1/3*55 = 25 + 18.333... = 43.333...
    #        l' = 2/3*55 = 36.666...
    #      Now: "H e l l o" with (92, 50, 43.333..., 36.666..., 110)
    #   2) Missing '!' at far right after o(110), edge insert n=1:
    #        o' = 110/2 = 55
    #        '!' = 110/2 = 55
    #
    # Pre-round durations: (92, 50, 43.333..., 36.666..., 55, 55)
    # Rounding (keep sum=332; >0.5 rounds up as carry):
    #   → (92, 50, 43, 37, 55, 55)
    T(
        "?He!lo??",
        (12, 80, 60, 30, 40, 70, 15, 25),
        "Hello!",
        (92, 50, 43, 37, 55, 55)
    )
