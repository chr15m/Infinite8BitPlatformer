from PodSix.Resource import *
from PodSix.Game import Game
from PodSix.Concurrent import Concurrent
from PodSix.Config import config

from engine.Player import Player
from engine.Notification import Notification
from engine.EditLayer import EditLayer
from engine.Hud import Hud
from engine.BitCamera import BitCamera
from engine.LevelManager import LevelManager

class Core(Game, EventMonitor, LevelManager):
	def __init__(self):
		config.zoom = 5
		gfx.Caption('Infinite 8-bit Platformer')
		gfx.SetSize([800, 450])
		gfx.LoadFont("freaky_fonts_ca", 16.0 / gfx.width, "default")
		gfx.LoadFont("FreeSans", 16.0 / gfx.width, "chat")
		sfx.LoadSound("item")
		sfx.LoadSound("portal")
		sfx.LoadSound("die")
		sfx.LoadSound("jump")
		Game.__init__(self)
		EventMonitor.__init__(self)
		self.editLayer = EditLayer(self)
		self.Add(self.editLayer)
		self.hud = Hud(self)
		self.Add(self.hud)
		self.Setup("Infinite 8-bit Platformer\n\na game\nby Chris McCormick", self.Instructions, 1.0)
		LevelManager.__init__(self)
		self.bgColor = (150, 150, 150)
	
	def Instructions(self):
		self.AddMessage("arrow keys move you\nenter key uses a portal\nescape key quits", None, 5.0)
	
	def Setup(self, message="", callback=None, time=None):
		self.player = Player(self, [0, 0, 11.0 / gfx.width, 12.0 / gfx.width])
		self.camera = BitCamera([0, 0, 1.0 / config.zoom, float(gfx.height) / gfx.width / config.zoom], tracking=self.player)
		if message:
			self.AddMessage(message, callback, time)
	
	def AddMessage(self, messagetxt, callback=None, time=None):
		self.Add(Notification(self, messagetxt, callback=callback, time=time))
	
	def RemoveMessage(self, message):
		self.Remove(message)
	
	def Quit(self):
		Game.Quit(self)
	
	###
	### Concurrency
	###
	
	def Pump(self):
		Game.Pump(self)
		EventMonitor.Pump(self)
	
	def Run(self):
		gfx.SetBackgroundColor(self.bgColor)
		Game.Run(self)
		gfx.Flip()
	
	def Update(self):
		Concurrent.Update(self)
	
	###
	### Platformer events
	###
	
	def PlayerDied(self):
		# if they don't have a last platform them pick the first platform on the level
		destination = self.player.lastplatform and self.player.lastplatform.id or self.levels[self.level].layer.platforms[0].id
		self.QueueLater(100, self.Restart, self.level, destination)
		self.UnSetLevel()
		self.Setup("oops!")
	
	def Restart(self, level, start):
		self.SetLevel(level, start)
	
	def Teleport(self, portal):
		parts = portal.destination.split(":")
		if len(parts) == 2:
			self.SetLevel(portal=portal, *parts)
			return True
	
	def Back(self):
		LevelManager.Back(self)
	
	###
	### Interface events
	###
	
	def KeyDown(self, e):
		#print e
		pass
	
	def KeyDown_escape(self, e):
		self.Quit()

