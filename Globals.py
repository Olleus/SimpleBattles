"""Constants used through out. Unlike configs does not vary between implementations"""

from enum import IntEnum


# Internal computation
POS_DEC_DIG: int = 3             # Position is rounded to this many decimal places

# Distance
# UNIT_HEIGHT = 1                # Height of all units
FILE_WIDTH: float = 5            # Width of file
RESERVE_DIST_BEHIND: float = 2   # How far behind a defeated unit a reserve will deploy
MIN_DEPLOY_DIST: float = 1       # Closest to edge of the map that reserves will deploy
SIDE_RANGE_PENALTY: float = 0.5  # Range penalty when attacking adjacent file

# Movement
BASE_SPEED: float = 20           # Default unit speed
CHARGE_DISTANCE: float = 2       # Distance from enemy at which units in NEUT break formation
HALT_POWER_GRADIENT: float = 20  # Units in DEFN stop moving when power drops at this rate

# Power
POWER_SCALE: float = 50          # This much power difference results in a 2:1 casualty ratio
LOW_MORALE_POWER: float = 200    # Power applied is *[0, 1] from morale
TERRAIN_POWER: float = 300       # Power applied is *O(0.1)*O(0.1) from roughness and rigidity+speed
HEIGHT_DIF_POWER: float = 20     # Power applied is *O(0.1) from height difference
RESERVES_POWER: float = 1/6      # Rate at which reserves give their own power to deployed unit
RESERVES_SOFT_CAP: float = 500   # Scale which determines how sharply the above diminishes

# Morale
PURSUE_MORALE: float = -0.25     # Morale loss inflicted when a unit starts pursing off the map
FILE_EMPTY: float = 0            # Morale for having an empty adjacent file
FILE_SUPPORTED: float = 0.1      # Morale for having an adjacent file protected by a friendly unit
FILE_VULNERABLE: float = -0.2    # Morale for having an adjacent file with a dangerously close enemy


class Stance(IntEnum):
    """The lower number, the more aggressively the unit will move"""
    AGGR = 0  # Units move at full speed always 
    NEUT = 1  # Units slow down to speed of slowest laggards, but charge once close to enemy
    DEFN = 2  # Units slow down to speed of slowest laggards, but halt when advantageous


class BattleOutcome(IntEnum):
    """The different potential situation after the battle has concluded"""
    BOTH_LOST = 0   # Both armies end the battle with no remaining units
    WIN_1 = 1       # Army 1 wins by having remaining units while army 2 does not
    WIN_2 = 2       # Army 2 wins by having remaining units while army 1 does not
    STALEMATE = 3   # Both armies have units remaining, but timed out or will not engage
