from PodSix.Platformer.Platform import Platform

from BitProp import BitProp

class BitPlatform(BitProp, Platform):
	color = [255, 255, 255]
	def __init__(self, *args, **kwargs):
		Platform.__init__(self, *args, **kwargs)
		BitProp.__init__(self, *args, **kwargs)

