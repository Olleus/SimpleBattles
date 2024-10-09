"""Constants which values may vary between implementations, left appart for convenience"""

"""1 / DELTA_T is roughly num of turns in battle
Larger delta_t is faster to compute and render as a gif, smaller values are smaller
As long as value is sufficiently small, should have negligible impact on actual result of battle
"""
DELTA_T = 0.005


"""Whether the frame counter is to be shown or not"""
FRAME_COUNTER = True
