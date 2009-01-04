from random import randint
from os import path

from PodSix.Resource import *
from PodSix.Game import Game
from PodSix.Concurrent import Concurrent
from PodSix.ArrayOps import Multiply, Subtract
from PodSix.SVGLoader import SVGLoader
from PodSix.TimedText import TimedText

from PodSix.Platformer.Level import Level
from PodSix.Platformer.Layer import Layer
from PodSix.Platformer.Platform import Platform
from PodSix.Platformer.Portal import Portal
from PodSix.Platformer.Item import Item
from PodSix.Platformer.Camera import Camera
from PodSix.Platformer.Prop import Prop
from PodSix.Platformer.Character import Character

def PropDraw(self):
	if isinstance(self.container, Layer):
		gfx.DrawRect(Multiply(Subtract(self.rectangle, self.container.level.camera.rectangle[:2] + [0, 0]), gfx.width), self.color, 0)

Prop.Draw = PropDraw

Platform.color = [200, 200, 255]
Portal.color = [200, 200, 200]
Item.color = [255, 255, 0]

class Player(Character):
	def __init__(self, game, *args, **kwargs):
		Character.__init__(self, *args, **kwargs)
		self.game = game
		self.inventory = []
		self.portal = None
	
	def Die(self):
		sfx.PlaySound("die")
		self.game.PlayerDied()
	
	def Draw(self):
		gfx.DrawRect(Multiply(Subtract(self.rectangle, self.level.camera.rectangle[:2] + [0, 0]), gfx.width), [255, 200, 200], 0)
	
	def Update(self):
		Character.Update(self)
		if self.velocity[1] > 4:
			self.Die()
		self.portal = None
	
	def Collide(self, who):
		Character.Collide(self, who)
		
		if isinstance(who, Item):
			self.game.AddMessage("got " + who.description)
			self.inventory.append(who)
			if len(self.inventory) == 14:
				self.game.Win()
			who.container.RemoveProp(who)
			sfx.PlaySound("item")
		
		if isinstance(who, Portal):
			self.portal = who
	
	def Do(self):
		if self.portal:
			sfx.PlaySound("portal")
			self.game.Teleport(self.portal)
			self.game.AddMessage("teleporting to " + self.portal.destination)

class MyCamera(Camera):
	def __init__(self, tracking):
		Camera.__init__(self, [0, 0, 1.0, float(gfx.height) / gfx.width], tracking=tracking)

class MyLevel(Level, SVGLoader):
	def __init__(self, name):
		Level.__init__(self, name)
		filename = path.join("resources", self.name + ".svg")
		self.LoadSVG(filename)
	
	def Layer_backgroundboxes(self, element, size, info, dom):
		l = Layer(self)
		for r in self.GetLayerRectangles():
			if r['details'][0] == "portal":
				p = Portal([x / size[0] for x in r['rectangle']], r['id'], r['details'][1])
				l.AddProp(p)
				self.startPoints[r['id']] = p
			elif r['details'][0] == "item":
				p = Item([x / size[0] for x in r['rectangle']], r['id'], r['details'][1])
				l.AddProp(p)
			else:
				p = Platform([x / size[0] for x in r['rectangle']], r['id'])
				l.AddProp(p)
				# platform is a start point
				if len(r['details']) > 1 and r['details'][1] == "start":
					self.startPoints["start"] = p
		
		self.AddLayer(info[1], l)

class Message(TimedText):
	messagecount = 0
	messagetop = 0
	spacing = 0.06
	
	def __init__(self, game, *args, **kwargs):
		self.game = game
		kwargs['position'] = {"centerx": 0.5, "top": 0.05 + Message.messagetop}
		kwargs['time'] = 0.2
		kwargs['color'] = [150, 150, 150]
		if kwargs.has_key('callback') and kwargs['callback']:
			self.callback = kwargs['callback']
		del kwargs['callback']
		TimedText.__init__(self, *args, **kwargs)
		Message.messagecount += 1
		Message.messagetop += self.spacing
	
	def TimeOut(self):
		Message.messagecount -= 1
		if Message.messagecount == 0:
			Message.messagetop = 0
		self.game.RemoveMessage(self)
		if hasattr(self, 'callback'):
			self.callback()

class Core(Game, EventMonitor):
	def __init__(self):
		self.colors = {"level1": [200, 200, 255], "level2": [150, 150, 150], "level3": [200, 255, 200]}
		gfx.Caption('MinimalistPlatformer - a game prototype by Chris McCormick')
		gfx.SetSize([640, 480])
		gfx.UseFont("Arial", 0.025, "default")
		sfx.LoadSound("item")
		sfx.LoadSound("portal")
		sfx.LoadSound("die")
		sfx.LoadSound("jump")
		Game.__init__(self)
		EventMonitor.__init__(self)
		self.Setup("MinimalistPlatformer\n\na game prototype\nby Chris McCormick", self.Instructions)
	
	def Instructions(self):
		self.AddMessage("use the arrow keys to move and the enter key to use a portal")

	def Setup(self, message="", callback=None):
		self.player = Player(self, [0, 0, 0.05, 0.0809])
		self.camera = MyCamera(self.player)
		self.levels = {}
		self.level = None
		for l in range(3):
			self.levels["level" + str(l + 1)] = MyLevel("level" + str(l + 1))
		self.SetLevel("level1", "start")	
		if message:
			self.AddMessage(message, callback)
	
	def AddMessage(self, messagetxt, callback=None):
		self.Add(Message(self, messagetxt, callback=callback))
	
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
		gfx.SetBackgroundColor([255, 255, 255])
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

