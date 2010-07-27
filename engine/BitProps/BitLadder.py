from PodSix.Platformer.Ladder import Ladder

from BitProp import BitProp

class BitLadder(BitProp, Ladder):
	color = [255, 255, 255]
	def __init__(self, *args, **kwargs):
		BitProp.__init__(self, *args, **kwargs)
		Ladder.__init__(self, *args)
