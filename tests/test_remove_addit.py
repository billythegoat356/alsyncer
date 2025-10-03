import pytest

from alsyncer.syncer import remove_additions
from alsyncer.models import CharAlignment


# --- Helpers -----------------------------------------------------------------

def AL(chars, durs):
    """Build an alignment list from parallel sequences of characters and durations."""
    assert len(chars) == len(durs)
    return [CharAlignment(character=c, duration=d) for c, d in zip(chars, durs)]

def chars_of(al):
    return [x.character for x in al]

def durs_of(al):
    return [x.duration for x in al]


# --- Basic & invariants -------------------------------------------------------

def test_no_additions_returns_same_content_and_object_identity():
    al = AL("ABC", [10, 20, 30])
    r = remove_additions(al, [])
    # Function returns the same list object when no additions are provided.
    assert r is al
    assert chars_of(r) == ["A", "B", "C"]
    assert durs_of(r) == [10, 20, 30]




@pytest.mark.parametrize(
    "chars,durs,additions",
    [
        ("ABCD", [10, 20, 30, 40], []),
        ("AAA",  [100, 200, 300], []),
        ("XYZ",  [1, 2, 3], []),
    ],
)
def test_total_duration_preserved(chars, durs, additions):
    al = AL(chars, durs)
    total_before = sum(durs_of(al))
    r = remove_additions(al, additions)
    total_after = sum(durs_of(r))
    assert total_after == total_before


# --- Single-index removals ----------------------------------------------------

def test_single_addition_at_beginning_rolls_into_next():
    al = AL("ABC", [100, 200, 300])
    r = remove_additions(al, [0])
    # 100 should be added to B
    assert chars_of(r) == ["B", "C"]
    assert durs_of(r) == [300, 300]


def test_single_addition_at_end_rolls_into_previous():
    al = AL("ABCD", [10, 20, 30, 40])
    r = remove_additions(al, [3])
    # 40 should be added to C
    assert chars_of(r) == ["A", "B", "C"]
    assert durs_of(r) == [10, 20, 70]


# --- Consecutive chunk removals (even/odd) -----------------------------------

def test_even_sized_chunk_in_middle_splits_left_half_to_left_and_right_half_to_right():
    # Remove [1,2]; left half (idx 1)=200 → goes to A; right half (idx 2)=300 → goes to D
    al = AL("ABCD", [100, 200, 300, 400])
    r = remove_additions(al, [1, 2])
    assert chars_of(r) == ["A", "D"]
    assert durs_of(r) == [300, 700]


def test_odd_sized_chunk_in_middle_splits_with_middle_split_between_neighbors():
    # Remove [1,2,3]; left part: [1]=200, right part: [3]=400, middle: [2]=300 (→ 150/150)
    al = AL("ABCDE", [100, 200, 300, 400, 500])
    r = remove_additions(al, [1, 2, 3])
    assert chars_of(r) == ["A", "E"]
    assert durs_of(r) == [450, 1050]  # A:100+200+150; E:500+400+150


def test_chunk_at_start_pushes_all_to_next():
    # Remove [0,1] → 10+20 added to C(30)
    al = AL("ABCD", [10, 20, 30, 40])
    r = remove_additions(al, [0, 1])
    assert chars_of(r) == ["C", "D"]
    assert durs_of(r) == [60, 40]


def test_chunk_at_end_pushes_all_to_previous():
    # Remove [2,3] → 30+40 added to B(20)
    al = AL("ABCD", [10, 20, 30, 40])
    r = remove_additions(al, [2, 3])
    assert chars_of(r) == ["A", "B"]
    assert durs_of(r) == [10, 90]


# --- Multiple disjoint chunks -------------------------------------------------

def test_multiple_disjoint_chunks_start_and_end_handled_separately():
    # Alignment: [A10, B20, C30, D40, E50, F60, G70]
    # Additions: [0,1] (start chunk) and [4,5] (end-side chunk)
    # - Start chunk [0,1] → 10+20 added to C (30→60)
    # - Chunk [4,5] → at indices 4,5 (E=50,F=60) → both to previous neighbor (D):
    #     because it's an end-side chunk? Careful: it's not at absolute end; right neighbor exists (G).
    #     Actually chunk [4,5] is internal and EVEN-sized → split:
    #       left half [4]=50 → to D; right half [5]=60 → to G
    al = AL("ABCDEFG", [10, 20, 30, 40, 50, 60, 70])
    r = remove_additions(al, [0, 1, 4, 5])
    # Remaining chars: C, D, G
    assert chars_of(r) == ["C", "D", "G"]
    # C: 30+(10+20)=60; D: 40+50=90; G: 70+60=130
    assert durs_of(r) == [60, 90, 130]
    # Total preserved
    assert sum(durs_of(r)) == sum([10, 20, 30, 40, 50, 60, 70])


def test_multiple_disjoint_chunks_with_odd_internal_chunk_and_boundaries():
    # Alignment: [A100, B200, C300, D400, E500, F600]
    # Additions: [0] (start), [2,3,4] (odd middle chunk)
    # - Start [0]: 100 → to B
    # - Middle [2,3,4]: left part [2]=300, right part [4]=500, middle= [3]=400 → 200/200 split
    #   Left neighbor: B (now 200+100 from start) gets +300 + 200 = +500 total
    #   Right neighbor: F gets +500 + 200 = +700 total
    al = AL("ABCDEF", [100, 200, 300, 400, 500, 600])
    r = remove_additions(al, [0, 2, 3, 4])
    assert chars_of(r) == ["B", "F"]
    assert durs_of(r) == [200 + 100 + 300 + 200, 600 + 500 + 200]  # [800, 1300]


# --- Rounding edge cases ------------------------------------------------------


# --- Non-uniform durations & character collapse example ----------------------

def test_non_uniform_durations_collapse_to_single_char():
    # Example provided by user: removing first three indices from A,A,C,C
    al = [
        CharAlignment(character="A", duration=100),
        CharAlignment(character="A", duration=100),
        CharAlignment(character="C", duration=100),
        CharAlignment(character="C", duration=100),
    ]
    r = remove_additions(al, [0, 1, 2])
    assert r == [CharAlignment(character="C", duration=400)]


# --- Error behavior -----------------------------------------------------------

def test_out_of_range_index_raises_index_error():
    al = AL("ABC", [10, 20, 30])
    with pytest.raises(IndexError):
        _ = remove_additions(al, [3])  # 3 is out of range for len=3


# --- Sanity/large-ish case ----------------------------------------------------

def test_largeish_case_multiple_chunks_mixed():
    # Alignment of size 10 with varied durations
    al = AL("ABCDEFGHIJ", [5, 10, 15, 20, 25, 30, 35, 40, 45, 50])
    # Remove three chunks: [0], [2,3], [7,8,9] (odd chunk at end edge)
    r = remove_additions(al, [0, 2, 3, 7, 8, 9])

    # Manual reasoning:
    # [0]: 5 → to index 1 (B=10 → 15)
    # [2,3]: even → left half [2]=15 to A-side neighbor (now index 1 after earlier step, B=15 → 30);
    #                 right half [3]=20 to right neighbor (index 4, E=25 → 45)
    # [7,8,9]: since it's to the end, entire sum (40+45+50=135) goes to previous kept neighbor (index 6, G=35 → 170)
    #
    # Remainings indices: 1(B), 4(E), 5(F), 6(G)
    assert chars_of(r) == ["B", "E", "F", "G"]
    assert durs_of(r) == [30, 45, 30, 170]
    assert sum(durs_of(r)) == sum([5,10,15,20,25,30,35,40,45,50])
