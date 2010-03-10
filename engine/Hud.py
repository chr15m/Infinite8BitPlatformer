from os import path

from PodSix.Resource import *
from PodSix.Concurrent import Concurrent
from PodSix.GUI.Button import ImageButton
from PodSix.GUI.Label import Label

from engine.ChatBox import ChatBox

class PortalDestinationIcon(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "portal.png")), Image(path.join("resources", "icons", "portal-invert.png"))], [60, 24])
		self.destination = None 
	
	def Pressed(self):
		# cancel the currently rememebered portal
		self.destination = None
	
	def Draw(self):
		if self.destination:
			ImageButton.Draw(self)

class EditButton(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "back.png")), Image(path.join("resources", "icons", "back-invert.png"))], [24, 24])
	
	def Pressed(self):
		self.parent.Back()

class LevelNameLabel(Label):
	def __init__(self, parent):
		self.parent = parent
		Label.__init__(self, "Loading...", pos={"left": 0.1, "top": 0.02}, color=[255, 255, 255])
	
	def MouseOver(self, e):
		self.parent.chatBox.ShowText(self.text, self.UpdateLevelName)
	
	def MouseOut(self, e):
		self.parent.chatBox.RevertText()
	
	def UpdateLevelName(self, name):
		self.parent.game.SetLevelName(name)

class Hud(Concurrent, EventMonitor):
	"""
	This layer holds the GUI for the player.
	"""
	def __init__(self, game):
		# whether edit mode is showing or not
		self.game = game
		Concurrent.__init__(self)
		EventMonitor.__init__(self)
		self.editButton = EditButton(self)
		self.chatBox = ChatBox(self)
		self.levelLabel = LevelNameLabel(self)
		self.portalDestinationIcon = PortalDestinationIcon(self)
		# edit button turns on the other buttons
		self.Add(self.editButton)
		self.Add(self.chatBox)
		self.Add(self.levelLabel)
		self.Add(self.portalDestinationIcon)
		self.priority = 2
	
	def SetPortalDestination(self, destination):
		self.portalDestinationIcon.destination = destination
	
	###
	###	Concurrency events
	###
	
	def Pump(self):
		Concurrent.Pump(self)
		EventMonitor.Pump(self)	
	
	def Update(self):
		Concurrent.Update(self)
	
	def Draw(self):
		Concurrent.Draw(self)
	
	def Back(self):
		self.game.Back()

