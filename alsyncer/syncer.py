
from .models import Alignment





def fit_alignment(
        alignment_text: str, reference_text: str, 
        alignment_gap: int = 0, reference_gap: int = 0
    ) -> tuple[list[int], list[int]]:
    """
    Fits the given alignment text to a reference text
    Returns a list of additions in the alignment text, and missing characters from the reference text, under the form of indexes
    
    Parameters:
        alignment_text: str
        reference_text: str
        alignment_gap: int = 0
        reference_gap: int = 0

    Returns:
        tuple[list[int], list[int]] - additions and missing chars
    """

    # Start fitting with the minimum length
    min_length = min(len(alignment_text), len(reference_text))

    # Regressively fit until there is nothing anymore
    for current_length in range(min_length, 0, -1):

        # The difference between the alignment text and the current length tells us how many substrings we can take
        diff = len(alignment_text) - current_length

        # Progressively cut substrings from left to right
        for start_i in range(diff+1):
            substring = alignment_text[start_i:start_i+current_length]

            # Try to index them in the reference text
            try:
                pos = reference_text.index(substring)
            except ValueError:
                continue
            
            has_before = pos != 0 or start_i != 0
            has_after = (
                pos + current_length < len(reference_text) or
                start_i + current_length < len(alignment_text)
            )

            additions: list[int] = []
            missing: list[int] = []

            # Fit part before
            if has_before:
                before_alignment_text = alignment_text[:start_i]
                before_reference_text = reference_text[:pos]
                _a, _m = fit_alignment(before_alignment_text, before_reference_text, alignment_gap, reference_gap)
                additions.extend(_a)
                missing.extend(_m)

            # Fit part after
            if has_after:
                this_alignment_gap = start_i+current_length
                this_reference_gap = pos+current_length

                after_alignment_text = alignment_text[this_alignment_gap:]
                after_reference_text = reference_text[this_reference_gap:]

                alignment_gap += this_alignment_gap
                reference_gap += this_reference_gap
                
                _a, _m = fit_alignment(after_alignment_text, after_reference_text, alignment_gap, reference_gap)
                additions.extend(_a)
                missing.extend(_m)

            return additions, missing

    # If nothing was fit, return everything
    return (
        [_a + alignment_gap for _a in range(len(alignment_text))],
        [_m + reference_gap for _m in range(len(reference_text))],
    )



def remove_additions(alignment: Alignment, additions: list[int]) -> Alignment:
    """
    Removes the list of given additions from the alignment

    Parameters:
        alignment: Alignment
        additions: list[int]

    Returns:
        Alignment
    """

    if not additions:
        return alignment
    
    # Alignment is full of additions, duration cannot be preserved, this is not possible
    if len(additions) == len(alignment):
        raise Exception("Alignment cannot be full of additions")

    # We process by chunks - if some additions are grouped together,
    # they need to be handled together so the extremities end up correctly distributed
    chunk_beginning = 0
    chunk_end = 1
    while chunk_beginning != len(additions):
        if (
            chunk_end == len(additions) or # Its the last one
            additions[chunk_end] > additions[chunk_end - 1] + 1 # Its not in a row (bigger)
        ):
            # Process now
            chunk_additions = additions[chunk_beginning:chunk_end]

            # If its from the beginning, just put everything to the next one
            if chunk_additions[0] == 0:
                addit_sum = sum(alignment[i].duration for i in chunk_additions)
                alignment[chunk_additions[-1]+1].duration += addit_sum
            # If its to the end, do the opposite
            elif chunk_additions[-1] == len(alignment)-1:
                addit_sum = sum(alignment[i].duration for i in chunk_additions)
                alignment[chunk_additions[0]-1].duration += addit_sum

            else:
                # Even
                if len(chunk_additions) % 2 == 0:
                    addit_sum_left = sum(alignment[i].duration for i in chunk_additions[:len(chunk_additions)//2])
                    addit_sum_right = sum(alignment[i].duration for i in chunk_additions[len(chunk_additions)//2:])
                    
                    alignment[chunk_additions[0]-1].duration += addit_sum_left
                    alignment[chunk_additions[-1]+1].duration += addit_sum_right

                # Odd
                else:
                    addit_sum_left = sum(alignment[i].duration for i in chunk_additions[:len(chunk_additions)//2])
                    addit_sum_right = sum(alignment[i].duration for i in chunk_additions[len(chunk_additions)//2+1:])
                    addit_middle = alignment[chunk_additions[len(chunk_additions)//2]].duration

                    # Preserve total
                    addit_sum_left += round(addit_middle / 2)
                    addit_sum_right += addit_middle - round(addit_middle / 2)
                    
                    alignment[chunk_additions[0]-1].duration += addit_sum_left
                    alignment[chunk_additions[-1]+1].duration += addit_sum_right

            # Reset chunk beginning
            chunk_beginning = chunk_end

        # Increment chunk end
        chunk_end += 1

    # Remove additions from alignment at the end
    alignment = [x for i, x in enumerate(alignment) if i not in additions]


    return alignment





def sync_alignment(alignment: Alignment, reference_text: str) -> Alignment:
    """
    Synchronises the given alignment to a reference text

    Parameters:
        alignment: Alignment
        reference_text: str

    Returns:
        Alignment
    """

    alignment_text = ''.join(alignment)

    # List of added characters in the alignment, aswell as missing ones
    additions, missing = fit_alignment(alignment_text, reference_text)

    raise NotImplementedError()

