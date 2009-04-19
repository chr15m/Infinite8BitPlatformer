from PodSix.Platformer.Item import Item

from BitProp import BitProp

class BitItem(BitProp, Item):
	color = [255, 255, 0]
	def __init__(self, *args, **kwargs):
		Item.__init__(self, *args, **kwargs)
		BitProp.__init__(self, *args, **kwargs)

