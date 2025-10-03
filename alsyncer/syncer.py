import math

from .models import Alignment, CharAlignment
from .utils import chunk, round_alignment as round_alignment_func




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





def remove_additions(alignment: Alignment, additions: list[int]) -> None:
    """
    Removes the list of given additions from the alignment
    NOTE: May adjust the alignment into containing floating point values
    Mutates in place

    Parameters:
        alignment: Alignment
        additions: list[int]
    """

    if not additions:
        return
    
    # Alignment is full of additions, duration cannot be preserved, this is not possible
    if len(additions) == len(alignment):
        raise Exception("Alignment cannot be full of additions")

    # We process by chunks - if some additions are grouped together,
    # they need to be handled together so the extremities end up correctly distributed
    for chunk_additions in chunk(additions):

        # If its from the beginning, just put everything to the next one
        if chunk_additions[0] == 0:
            addit_sum = sum(alignment[i].duration for i in chunk_additions)
            alignment[chunk_additions[-1]+1].duration += addit_sum

        # If its to the end, do the opposite
        elif chunk_additions[-1] == len(alignment)-1:
            addit_sum = sum(alignment[i].duration for i in chunk_additions)
            alignment[chunk_additions[0]-1].duration += addit_sum

        else:
            addit_sum_left = sum(
                alignment[i].duration for i in 
                chunk_additions[:math.floor(len(chunk_additions)/2)]
            )
            addit_sum_right = sum(
                alignment[i].duration for i in 
                chunk_additions[math.ceil(len(chunk_additions)/2):]
            )

            # If odd, split the middle
            if len(chunk_additions) % 2 == 1:
                addit_middle = alignment[chunk_additions[len(chunk_additions)//2]].duration
                addit_sum_left += addit_middle / 2
                addit_sum_right += addit_middle / 2

            alignment[chunk_additions[0]-1].duration += addit_sum_left
            alignment[chunk_additions[-1]+1].duration += addit_sum_right


    # Remove additions from alignment at the end
    for i in reversed(additions): # Reverse to not have to carry gap
        alignment.pop(i)



def add_missing(alignment: Alignment, reference_text: str, missing: list[int]) -> None:
    """
    Adds all the missing characters from the reference text to the alignment
    Handles durations distribution
    NOTE: May adjust the alignment into containing floating point values
    Mutates in place

    Parameters:
        alignment: Alignment
        reference_text: str
        missing: list[int]
    """

    if not missing:
        return
    
    # Alignment is empty, we cannot distribute anything
    if not alignment:
        raise Exception("Alignment cannot be empty")

    chunked_missing = chunk(missing)

    # We also process by chunks
    for chunk_i, chunk_missing in enumerate(chunked_missing):

        # Whether the prev char was also distributed before
        prev_char_distributed = (
            chunk_i != 0 and  # Is not the first
            chunked_missing[chunk_i-1][-1] == chunk_missing[0] - 2 # The last index of the previous missing chunk has only 2 diff with the current first
        )
        # Same for next char
        next_char_distributed = (
            chunk_i != len(chunked_missing) - 1 and # Is not the last
            chunked_missing[chunk_i+1][0] == chunk_missing[-1] + 2 # The first index of the next missing chunk has only 2 diff with the current last
        )


        # If its from the beginning, split evenly with the next one
        if chunk_missing[0] == 0:
            # Get next char
            next_char = alignment[0]

            if next_char_distributed:
                # If next one is distributed aswell, different handling
                next_chunk = chunked_missing[chunk_i+1]

                # If next chunk ends
                if next_chunk[-1] == len(reference_text) - 1:
                    # It will be split evenly with next chunk aswell
                    duration_per_char = next_char.duration / (len(chunk_missing) + 1 + len(next_chunk)) # Account for this chunk, next one, and the char.

                # Next chunk is distributed on both ends
                else:
                    # Take in account its own half of next chunk
                    # We use 2 because in some cases next chunk may be odd and one would take 1/X
                    duration_per_char = 2 / (
                        2 * (len(chunk_missing))
                        + 2
                        + len(next_chunk)
                    ) * next_char.duration

            else:
                duration_per_char = next_char.duration / (len(chunk_missing) + 1)

            # Add in the beginning
            alignment[0:0] = [
                CharAlignment(character=reference_text[i], duration=duration_per_char)
                for i in chunk_missing
            ]

            # Override next char only if not distributed (it will be done later)
            if not next_char_distributed:
                next_char.duration = duration_per_char

        # If its to the end, do the opposite
        elif chunk_missing[-1] == len(reference_text)-1:
            # Get prev char
            prev_char = alignment[-1]

            if prev_char_distributed:
                # If prev one is distributed aswell, different handling
                prev_chunk = chunked_missing[chunk_i-1]

                # If prev chunk starts
                if prev_chunk[0] == 0:
                    # It will be split evenly with prev chunk aswell
                    duration_per_char = prev_char.duration / (len(chunk_missing) + 1 + len(prev_chunk))

                # Prev chunk is distributed on both ends
                else:
                    # Take in account its own half of prev chunk
                    # We use 2 because in some cases next chunk may be odd and one would take 1/X
                    duration_per_char = 2 / (
                        2 * (len(chunk_missing))
                        + 2
                        + len(prev_chunk)
                    ) * prev_char.duration

            else:
                duration_per_char = prev_char.duration / (len(chunk_missing) + 1)

            # Add in the end
            alignment[len(alignment):len(alignment)] = [
                CharAlignment(character=reference_text[i], duration=duration_per_char)
                for i in chunk_missing
            ]

            # Override prev char
            prev_char.duration = duration_per_char

        # It's anywhere in the middle
        else:
            # Get surrounding chars
            prev_char = alignment[chunk_missing[0] - 1]
            next_char = alignment[chunk_missing[0]]

            prev_dur = prev_char.duration
            next_dur = next_char.duration

            # Get dividers for both
            # 2 is for the edge, then we take length because we only take half but multiplied by two. Only 1 if odd
            prev_div = len(chunk_missing) + 2
            next_div = len(chunk_missing) + 2

            # If they were also borders before, or are after, add the next chunk missing
            if prev_char_distributed:
                prev_chunk = chunked_missing[chunk_i-1]
                # Previous one starts from the start
                if prev_chunk[0] == 0:
                    prev_div += 2 * len(prev_chunk)
                # Prev one distributed evenly
                else:
                    prev_div += len(prev_chunk)
            
            if next_char_distributed:
                next_chunk = chunked_missing[chunk_i+1]
                if next_chunk[-1] == len(reference_text) - 1:
                    next_div += 2 * len(next_chunk)
                else:
                    next_div += len(next_chunk)

            # Update them
            prev_char.duration = 2 / prev_div * prev_dur

            if not next_char_distributed:
                next_char.duration = 2 / next_div * next_dur

            # Update new chars
            new_chars: Alignment = []
            for i, missing_index in enumerate(chunk_missing):
                char = reference_text[missing_index]
                mid = (len(chunk_missing) + 1 ) / 2

                # Only take from prev
                if i + 1 < mid:
                    dur = 2 / prev_div * prev_dur

                # Take from both (odd)
                elif i + 1 == mid:
                    dur = prev_dur / prev_div + next_dur / next_div

                # Only from next
                elif i + 1 > mid:
                    dur = 2 / next_div * next_dur

                new_chars.append(
                    CharAlignment(character=char, duration=dur)
                )

            alignment[chunk_missing[0]:chunk_missing[0]] = new_chars







def sync_alignment(alignment: Alignment, reference_text: str, round_alignment: bool = True) -> Alignment:
    """
    Synchronises the given alignment to a reference text

    Parameters:
        alignment: Alignment
        reference_text: str
        round_alignment: bool = True - whether to round the final alignment to include only integers.
                                       Missing/additions distribution introduces floating point durations,
                                       And usually you want the durations to be integers (milliseconds)

    Returns:
        Alignment
    """

    alignment_text = ''.join(alignment)

    # List of added characters in the alignment, aswell as missing ones
    additions, missing = fit_alignment(alignment_text, reference_text)

    remove_additions(alignment, additions)
    add_missing(alignment, reference_text, missing)

    if round_alignment:
        round_alignment_func(alignment)


