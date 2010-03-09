from os import path

from PodSix.Platformer.Portal import Portal
from PodSix.GUI.Button import ImageButton
from PodSix.Resource import *

from BitProp import BitProp

class PortalIcon(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "portal.png")), Image(path.join("resources", "icons", "portal-invert.png"))], [0, 0])
	
	def Pressed(self):
		# cancel the currently rememebered portal
		print 'pressed'
	
	def Draw(self, really=False):
		if really:
			ImageButton.Draw(self)

class BitPortal(BitProp, Portal):
	color = [255, 0, 0]
	def __init__(self, *args, **kwargs):
		BitProp.__init__(self, *args, **kwargs)
		Portal.__init__(self, *args)
		self.icon = PortalIcon(self)
		self.Add(self.icon)
	
	def MouseMove(self, e):
		print 'yes'
	
	def DrawEdit(self):
		BitProp.DrawEdit(self)
		# draw the portal connected icon
		self.icon.pos = [self.box[0] + 16, self.box[1] + 16]
		self.icon.Draw(True)
