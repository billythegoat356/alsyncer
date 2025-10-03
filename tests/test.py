from alsyncer import CharAlignment

alignment = [
    CharAlignment(character="H", duration=100),
    CharAlignment(character="i", duration=50)
]

from alsyncer import sync_alignment

reference_text = "Hi!"
sync_alignment(alignment, reference_text)

from rich import print
print(alignment)
# [
#     CharAlignment(character="H", duration=100),
#     CharAlignment(character="i", duration=25),
#     CharAlignment(character="!", duration=25)
# ]