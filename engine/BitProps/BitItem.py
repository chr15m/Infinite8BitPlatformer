from PodSix.Platformer.Item import Item

from BitProp import BitProp

class BitItem(BitProp, Item):
	color = [255, 255, 0]
	def __init__(self, *args, **kwargs):
		Item.__init__(self, *args, **kwargs)
		BitProp.__init__(self, *args, **kwargs)
		self.visible = True
	
	def Draw(self):
		if self.visible:
			BitProp.Draw(self)
		else:
			self.box = None
	
	def Hide(self):
		self.visible = False
