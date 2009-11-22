from os import path

from PodSix.Resource import *
from PodSix.Concurrent import Concurrent
from PodSix.GUI.Button import ImageButton

class EditButton(ImageButton):
	def __init__(self, parent):
		self.parent = parent
		ImageButton.__init__(self, [Image(path.join("resources", "icons", "back.png")), Image(path.join("resources", "icons", "back-invert.png"))], [24, 24])
	
	def Pressed(self):
		self.parent.Back()

class Hud(Concurrent, EventMonitor):
	"""
	This layer holds the GUI for the player.
	"""
	def __init__(self, game):
		# whether edit mode is showing or not
		self.game = game
		self.editButton = EditButton(self)
		Concurrent.__init__(self)
		EventMonitor.__init__(self)
		# edit button turns on the other buttons
		self.Add(self.editButton)
		self.priority = 2
	
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

