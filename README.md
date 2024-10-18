# SIMPLE BATTLES
v0.7.3

Exploring the simplest video-gamey "Battle Simulator" which requires minimal, has interesting emergent behaviour which aligns with a simplified picture of historical reality, works for as many different contexts as possible, and all the while having the fewest and most intuitive rules possible.

Browser based implementation available at [olleus.pyscriptapps.com/simple-battles/](olleus.pyscriptapps.com/simple-battles/).

Main entry point into the code is Battle.Battle().do() and its child GraphicBattle(). A complete example of how to define armies, landscape and fight a battle with them is given in example_battle.py.

Requires python v3.12 with:
* attrs v23.1
* pillow v10.4
* and their dependencies

Written in accordance with mypy v1.10 and flake8 v7.1.
