from PodSix.Platformer.Item import Item
from PodSix.Resource import *

from BitProp import BitProp

class BitItem(BitProp, Item, EventMonitor):
	color = [255, 255, 0]
	def __init__(self, *args, **kwargs):
		BitProp.__init__(self, *args, **kwargs)
		Item.__init__(self, *args)
		EventMonitor.__init__(self)
		self.chatBox = kwargs['editLayer'].levelmanager.hud.chatBox
		self.over = False
		self.visible = True
		self.showCounter = 0
	
	def InRect(self, pos):
		if self.box:
			return pos[0] < (self.box[0] + self.box[2]) and pos[0] > self.box[0] and pos[1] < self.box[1] + self.box[3] and pos[1] > self.box[1]
	
	def Pump(self):
		Item.Pump(self)
		EventMonitor.Pump(self)	
	
	def SetEditLayer(self, layer):
		BitProp.SetEditLayer(self, layer)
	
	def MouseMove(self, e):
		over = self.InRect(e.pos)
		if self.over != over and self.visible and self.editLayer.mode:
			self.over = over
			if over:
				self.chatBox.ShowText(self.description, self.UpdateDescription)
			else:
				self.chatBox.RevertText()
	
	def UpdateDescription(self, description):
		self.description = description
		self.chatBox.RevertText()
	
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

