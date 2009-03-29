from PodSix.Resource import *
from PodSix.Game import Game
from PodSix.Concurrent import Concurrent
from PodSix.ArrayOps import Multiply, Subtract
from PodSix.Platformer.Layer import Layer
from PodSix.Platformer.Platform import Platform
from PodSix.Platformer.Portal import Portal
from PodSix.Platformer.Item import Item
from PodSix.Platformer.Camera import Camera
from PodSix.Platformer.Prop import Prop

from engine.Player import Player
from engine.Notification import Notification
from engine.BitLevel import BitLevel

def PropDraw(self):
	if isinstance(self.container, Layer):
		gfx.DrawRect(Multiply(Subtract(self.rectangle, self.container.level.camera.rectangle[:2] + [0, 0]), gfx.width), self.color, 0)

Prop.Draw = PropDraw

Platform.color = [200, 200, 255]
Portal.color = [200, 200, 200]
Item.color = [255, 255, 0]

class Core(Game, EventMonitor):
	def __init__(self):
		self.colors = {"level1": [200, 200, 255], "level2": [150, 150, 150], "level3": [200, 255, 200]}
		gfx.Caption('Infinite8bitPlatformer')
		gfx.SetSize([800, 450])
		gfx.LoadFont("freaky_fonts_ca", 16.0 / gfx.width, "default")
		sfx.LoadSound("item")
		sfx.LoadSound("portal")
		sfx.LoadSound("die")
		sfx.LoadSound("jump")
		Game.__init__(self)
		EventMonitor.__init__(self)
		self.Setup("Infinite8bitPlatformer\n\na game\nby Chris McCormick", self.Instructions, 0.3)
	
	def Instructions(self):
		self.AddMessage("arrow keys move you\nenter key uses a portal\nescape key quits", None, 0.8)
	
	def Setup(self, message="", callback=None, time=None):
		self.player = Player(self, [0, 0, 0.05, 0.0809])
		self.camera = Camera([0, 0, 1.0, float(gfx.height) / gfx.width], tracking=self.player)
		self.levels = {}
		self.level = None
		for l in range(3):
			self.levels["level" + str(l + 1)] = BitLevel("level" + str(l + 1))
		self.SetLevel("level1", "start")	
		if message:
			self.AddMessage(message, callback, time)
	
	def AddMessage(self, messagetxt, callback=None, time=None):
		self.Add(Notification(self, messagetxt, callback=callback, time=time))
	
	def RemoveMessage(self, message):
		self.Remove(message)
	
	def SetLevel(self, level, start):
		if self.level:
			self.Remove(self.levels[self.level])
			self.levels[self.level].RemovePlayerCamera()
		self.level = level
		self.levels[self.level].SetPlayerCamera(self.player, self.camera, start)
		self.Add(self.levels[self.level])
		Platform.color = self.colors[self.level]
	
	def Win(self):
		[self.Remove(o) for o in self.objects]
		self.AddMessage("you collected all items\n\n\nyou win :)", self.WinDone)
	
	def WinDone(self):
		self.Quit()
	
	def PlayerDied(self):
		self.Remove(self.levels[self.level])
		self.levels[self.level].RemovePlayerCamera()
		self.Setup("oops!")
	
	def Teleport(self, portal):
		self.SetLevel(*portal.destination.split(":"))
	
	def Pump(self):
		Game.Pump(self)
		EventMonitor.Pump(self)
	
	def Run(self):
		gfx.SetBackgroundColor([15, 15, 15])
		Game.Run(self)
		gfx.Flip()
	
	def KeyDown(self, e):
		#print e
		pass
	
	def KeyDown_escape(self, e):
		self.Quit()
	
	def KeyDown_right(self, e):
		self.player.WalkRight()
	
	def KeyDown_left(self, e):
		self.player.WalkLeft()
	
	def KeyUp_right(self, e):
		self.player.StopRight()
	
	def KeyUp_left(self, e):
		self.player.StopLeft()
	
	def KeyDown_up(self, e):
		if self.player.platform:
			sfx.PlaySound("jump")
		self.player.Jump()
	
	def KeyDown_return(self, e):
		self.player.Do()

