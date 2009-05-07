from PodSix.Platformer.Portal import Portal

from BitProp import BitProp

class BitPortal(BitProp, Portal):
	color = [255, 0, 0]
	def __init__(self, *args, **kwargs):
		BitProp.__init__(self, *args, **kwargs)
		Portal.__init__(self, *args)

