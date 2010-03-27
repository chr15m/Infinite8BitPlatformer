from PodSix.Platformer.Item import Item
from PodSix.Resource import *

from BitProp import BitProp

class BitItem(BitProp, Item):
	color = [255, 255, 0]
	def __init__(self, *args, **kwargs):
		BitProp.__init__(self, *args, **kwargs)
		Item.__init__(self, *args)
		self.visible = True
		self.showCounter = 0
	
	def Draw(self):
		if self.visible:
			BitProp.Draw(self)
		else:
			if self.showCounter > 0:
				self.showCounter -= self.Elapsed()
			else:
				self.showCounter = 0
				self.Show()
			self.box = None
	
	def Hide(self):
		self.showCounter = 30
		self.visible = False
	
	def Show(self):
		self.visible = True

