


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