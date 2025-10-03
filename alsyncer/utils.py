import math

from .models import Alignment, CharAlignment


def chunk(indexes: list[int]) -> list[list[int]]:
    """
    Chunks a list of indexes into a list of lists with indexes that are in a row (contiguous)
    NOTE: Expects the indexes to be sorted
    
    Parameters:
        indexes: list[int]
        
    Returns:
        list[list[int]]
    """

    final_chunks: list[list[int]] = []

    chunk_beginning = 0
    chunk_end = 1

    while chunk_beginning != len(indexes):
        if (
            chunk_end == len(indexes) or # Its the last one
            indexes[chunk_end] > indexes[chunk_end - 1] + 1 # Its not in a row (bigger)
        ):
            chunk_indexes = indexes[chunk_beginning:chunk_end]
            final_chunks.append(chunk_indexes)

            # Reset chunk beginning
            chunk_beginning = chunk_end

        # Increment chunk end
        chunk_end += 1

    return final_chunks



EPS = 1e-9

def round_alignment(alignment: Alignment) -> Alignment:
    """
    After processing, the alignment may contain floating point number
    This function takes care of rounding those to ensure the alignment contains only integers, which are often needed for further processing.
    NOTE: The sum of all the durations of the alignment is required to be an integer

    The rounding happens towards the center - a bias is carried, whenever it exceeds 0.5, the current number gets added 1
    This ensures local smoothness.

    Parameters:
        alignment: Alignment

    Returns:
        Alignment

    -----------

    Examples:
        (the following examples only contain lists of durations)

        [1, 2,5] -> error
        [1.2, 2.4, 3.4] -> [1, 3, 3]
        [0.5, 1.5] -> [2] (because 0.5 does not exceed 0.5)
    """

    sum_durs = sum(al.duration for al in alignment)
    if not math.isclose(sum_durs, round(sum_durs), abs_tol=EPS):
        raise Exception("The sum of all the durations of the alignment is not an integer!")

    bias = 0
    new_alignment: Alignment = []
    for al in alignment:
        bias += al.duration - int(al.duration)

        new_duration = int(al.duration)

        if bias > 0.5 - EPS:
            bias -= 1
            new_duration += 1

        new_alignment.append(CharAlignment(
            character=al.character,
            duration=new_duration
        ))

    return new_alignment
