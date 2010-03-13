from os import path

from PodSix.Platformer.Portal import Portal
from PodSix.Platformer.Layer import Layer
from PodSix.GUI.Button import ImageButton
from PodSix.Resource import *

from BitProp import BitProp

class PortalIcon(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "portal.png")), Image(path.join("resources", "icons", "portal-invert.png"))], [0, 0])
	
	def Pressed(self):
		# cancel the currently remembered portal
		if self.parent.container and self.parent.container.__class__ == Layer:
			# tell the edit layer what portal destination is
			# TODO: shit, why is this so complicated? bad design i guess!
			self.parent.container.level.editLayer.SetPortalDestination(self.parent.container.level.name + ":" + self.parent.id)
	
	def Draw(self, really=False):
		if really:
			ImageButton.Draw(self)

class BitPortal(BitProp, Portal, EventMonitor):
	color = [255, 0, 0]
	def __init__(self, *args, **kwargs):
		self.over = False
		BitProp.__init__(self, *args, **kwargs)
		Portal.__init__(self, *args)
		EventMonitor.__init__(self)
		self.icon = PortalIcon(self)
		self.Add(self.icon)
	
	def InRect(self, pos):
		if self.box:
			return pos[0] < (self.box[0] + self.box[2]) and pos[0] > self.box[0] and pos[1] < self.box[1] + self.box[3] and pos[1] > self.box[1]
	
	def Pump(self):
		Portal.Pump(self)
		EventMonitor.Pump(self)	
	
	def MouseMove(self, e):
		self.over = self.InRect(e.pos) or self.icon.InRect(e.pos)
	
	def DrawEdit(self):
		BitProp.DrawEdit(self)
		# draw the portal connected icon
		if self.over and self.box:
			self.icon.pos = [self.box[0] + 16, self.box[1] - 16]
			self.icon.Draw(True)
