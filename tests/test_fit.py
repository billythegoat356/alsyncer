# test_fit_alignment.py
import itertools
import random
import string

import pytest

from alsyncer.syncer import fit_alignment  # change to actual import path


# ----------------------------
# Helper to ease assertions
# ----------------------------
def assert_result(alignment_text, reference_text, exp_additions, exp_missing):
    additions, missing = fit_alignment(alignment_text, reference_text)
    assert additions == exp_additions, f"Additions mismatch for {alignment_text!r} vs {reference_text!r}"
    assert missing == exp_missing, f"Missing mismatch for {alignment_text!r} vs {reference_text!r}"


# ----------------------------
# Trivial / empty cases
# ----------------------------

def test_both_empty():
    assert_result("", "", [], [])


def test_alignment_empty_only_missing():
    assert_result("", "abc", [], [0, 1, 2])


def test_reference_empty_only_additions():
    assert_result("abc", "", [0, 1, 2], [])


# ----------------------------
# Perfect matches
# ----------------------------

@pytest.mark.parametrize("s", ["a", "abc", "hello", "repetitionnnn", "😀👍"])
def test_identical_strings_no_diffs(s):
    assert_result(s, s, [], [])


# ----------------------------
# Single insertions (additions) in alignment
# ----------------------------

def test_addition_in_middle():
    # alignment has 'X' at index 2
    assert_result("abXc", "abc", [2], [])


def test_addition_at_prefix():
    assert_result("Xabc", "abc", [0], [])


def test_addition_at_suffix():
    assert_result("abcX", "abc", [3], [])


# Multiple additions
def test_multiple_additions():
    # extras at 1, 2, and 5
    assert_result("aXYbcZ", "abc", [1, 2, 5], [])


# ----------------------------
# Single deletions (missing) from reference
# ----------------------------

def test_missing_in_middle():
    # reference has 'X' at index 2
    assert_result("abc", "abXc", [], [2])


def test_missing_at_prefix():
    assert_result("abc", "Xabc", [], [0])


def test_missing_at_suffix():
    assert_result("abc", "abcX", [], [3])


# Multiple missing
def test_multiple_missing():
    # missing reference indices 1, 2, and 5
    assert_result("abc", "aXYbcZ", [], [1, 2, 5])


# ----------------------------
# Substitutions (character differs at same fitted position)
# Treated as 1 addition + 1 missing at the same logical slot
# ----------------------------

def test_single_substitution():
    # 'b' (alignment idx 1) vs 'd' (reference idx 1)
    assert_result("abc", "adc", [1], [1])


@pytest.mark.parametrize(
    "a,r,exp",
    [
        ("café", "cafe", ([3], [3])),     # 'é' vs 'e'
        ("kitten", "sitten", ([0], [0])), # 'k' vs 's'
        ("color", "colour", ([], [4])),   # one extra in reference (British vs American)
        ("colour", "color", ([4], [])),   # inverse
    ],
)
def test_unicode_and_length_variants(a, r, exp):
    assert_result(a, r, exp[0], exp[1])


# ----------------------------
# Repeated characters / ambiguous fits
# ----------------------------

def test_repeated_chars_reference_longer():
    # alignment fits into reference; reference has one extra trailing 'a' => missing [3]
    assert_result("aaa", "aaaa", [], [3])


def test_repeated_chars_alignment_longer():
    # alignment has one extra trailing 'a' => additions [3]
    assert_result("aaaa", "aaa", [3], [])


def test_repeated_blocks_with_internal_additions():
    # Extra hyphens considered additions at indices 2 and 3
    assert_result("ab--cd", "abcd", [2, 3], [])


# ----------------------------
# No overlap at all
# ----------------------------

def test_disjoint_strings():
    # no common substring -> everything is addition/missing
    assert_result("xyz", "abc", [0, 1, 2], [0, 1, 2])


# ----------------------------
# Complex mixed scenarios
# ----------------------------

def test_mixed_additions_and_missing():
    # alignment:   a   b X c   Y  d   Z e
    # indices:     0   1 2 3   4  5   6 7
    # reference:   a   b   c W    d    e Q
    # indices:     0   1   2 3    4    5 6
    # Expect:
    #   additions: [2, 4, 6] (X, Y, Z)
    #   missing:   [3, 6]    (W, Q)
    assert_result("abXcYdZe", "abcWd eQ".replace(" ", ""), [2, 4, 6], [3, 6])


# ----------------------------
# Structural invariants (property-like checks)
# ----------------------------

@pytest.mark.parametrize("a_len,r_len", list(itertools.product(range(0, 7), repeat=2)))
def test_index_bounds_and_types(a_len, r_len):
    a = "".join(random.choice(string.ascii_lowercase) for _ in range(a_len))
    r = "".join(random.choice(string.ascii_lowercase) for _ in range(r_len))
    additions, missing = fit_alignment(a, r)
    # All additions are in range(len(a)); all missing are in range(len(r))
    assert all(isinstance(i, int) and 0 <= i < len(a) for i in additions)
    assert all(isinstance(i, int) and 0 <= i < len(r) for i in missing)
    # No duplicates; monotonic non-decreasing ordering is desirable and simplifies consumers
    assert additions == sorted(set(additions))
    assert missing == sorted(set(missing))


def test_idempotence_when_equal():
    # Calling twice on equals should stay empty
    a, r = "the quick brown fox", "the quick brown fox"
    assert_result(a, r, [], [])
    assert_result(a, r, [], [])


# ----------------------------
# Regression expectations capturing algorithm intent
# ----------------------------

def test_large_shared_middle_with_noise_both_sides():
    # Shared core "middle" should be kept; noise at edges identified correctly
    assert_result("XXmiddleYY", "ZmiddleW", [0, 1, 8, 9], [0, 7])
