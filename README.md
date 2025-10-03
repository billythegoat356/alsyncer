# alsyncer
A homemade algorithm that synchronises a text alignment with a reference text.   
Uses Symmetric Alignment Distribution.   

# Idea
Most STT algorithms don't support receiving a reference text, meaning you have to trust their given characters alignment.   
However, sometimes you already have the text that is being said in the audio, but you don't have the alignment, so you end up using these STT that output a slightly different text.   
But what if you need the exact same text that you have?   
This algorithm solves this issue.   

# Installation
```sh
git clone https://github.com/billythegoat356/alsyncer
cd alsyncer
pip install .
```

# Usage
First, turn your alignment structure into what alsyncer expects.   
```py
from alsyncer import CharAlignment

alignment = [
    CharAlignment(character="H", duration=100),
    CharAlignment(character="i", duration=50)
]
```
The duration can be of whatever unit, but it is recommended to use integers that represent milliseconds.   

Then, sync it with a reference text:
```py
from alsyncer import sync_alignment

reference_text = "Hi!"
sync_alignment(alignment, reference_text)

print(alignment)
# [
#     CharAlignment(character="H", duration=100),
#     CharAlignment(character="i", duration=25),
#     CharAlignment(character="!", duration=25)
# ]
```
Note that the alignment will always end up getting rounded to eliminate floating point numbers introduced from duration distribution.   
It will however maintain identical total duration.   

If, for some reason, you want to sync an alignment containing floating point numbers, pass the following parameter:
```py
sync_alignment(alignment, reference_text, round_alignment=False)
```
This will disable alignment rounding at the end.

# Algorithm

## Process
Alsyncer follows a heuristic homemade process.   
It expects an alignment as input, aswell as a reference text:
- It first checks which parts from the alignment don't appear in the reference text, these are **additions**
- It then checks which parts from the reference text are **missing** from the alignment
- Then, it **removes all the additions** and distributes the durations
- Finally, it **inserts the missing characters** and distributes durations from their neighbours
- (optional) At the end, it rounds the durations to ensure the alignment only contains integer values. It also conservs total duration.

Note that when distributing/inserting durations, the algorithm doesn't look at the character to determine adequate duration ratio, but it splits it evenly with the characters at the edges, which may not be accurate in some cases.   

## Gather additions and missing characters
The alignment and reference text is broken up using a custom Greedy LCS algorithm, until only a part of the alignment remains (the **additions** in this case), or a part of the reference text (the **missing** characters).   

## Additions removal
This algorithm is homemade.   
The following is an example and not the mathematical formula.   

Say you have:   
`AkkB`   
With `kk` being two characters that need to be removed.   
The duration of the first `k` will be added to the duration of `A`.   
Same for the second `k` and `B`.   

If the number of `k`s is odd, the one in the middle will be distributed evenly to `A` and `B`.   

If the `k`s are in the far left or right, they get distributed to their only neighbour.   

## Missing characters insertion
This algorithm is also homemade.   
The following is an example and not the mathematical formula.   
This algorithm follows an even distribution, but in some cases, a logarithmic distribution algorithm could also be accurate.   

Say you have:   
`AkkB`   
With `kk` being two characters that need to be inserted.   
The duration of `A` will become `2/4` of what it was.   
Same for `B`.   

The duration of `k1` will become `2/4` of the duration of `A` since its closer to it.   
Same for `k2` with `B`.   


Now with an odd amount of `k`s.   
`AkkkB`   
The duration of `A` will become `2/5` of what it was.   
Same for `B`.   

The duration of `k1` will become `2/5` of the duration of `A`.   
Same for `k3` with `B`.   

The duration of `k2` will become `1/5` of the duration of `A` plus `1/5` of the duration of `B`.   

If the `k`s are in the far left or right, their nearest neighbour gets evenly distributed to them.   


If we have this pattern:   
`AkkBkC`   
`B` takes in account all of its neighbours.   


## Etc
I've coded this in a few hours so feel free to PR if you've found any bugs or improvments to this algorithm.   

## Ideas
Other ideas I had:   

In the context of STT alignment, it may also happen (maybe even more) that one neighbour wrongfully gets a higher duration, or lower duration, meaning that it has missing characters, or additions right next to it.   
As opposed to the current algorithm that distributes evenly with both neighbours, we could focus on the neighbour with the lower duration (in the case of removing characters) or on the neighbour with the higher duration (if adding missing characters).   

However this would require linguistic analysis (e.g., a `.` is expected to have a higher duration than a `a`).