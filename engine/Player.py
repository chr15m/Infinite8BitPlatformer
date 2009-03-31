from PodSix.Resource import *
from PodSix.Platformer.Character import Character
from PodSix.Platformer.Portal import Portal
from PodSix.Platformer.Item import Item
from PodSix.ArrayOps import Multiply, Subtract

class Player(Character, EventMonitor):
	def __init__(self, game, *args, **kwargs):
		Character.__init__(self, *args, **kwargs)
		EventMonitor.__init__(self)
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
	
	def Pump(self):
		Character.Pump(self)
		EventMonitor.Pump(self)
	
	def Collide(self, who):
		Character.Collide(self, who)
		
		if isinstance(who, Item):
			self.game.AddMessage("got " + who.description)
			self.inventory.append(who)
			if len(self.inventory) == 15:
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
	
	###
	### Key events etc.
	###
	
	def KeyDown_right(self, e):
		self.WalkRight()
	
	def KeyDown_left(self, e):
		self.WalkLeft()
	
	def KeyUp_right(self, e):
		self.StopRight()
	
	def KeyUp_left(self, e):
		self.StopLeft()
	
	def KeyDown_up(self, e):
		if self.platform:
			sfx.PlaySound("jump")
		self.Jump()
	
	def KeyDown_return(self, e):
		self.Do()

