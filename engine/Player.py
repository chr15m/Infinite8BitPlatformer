from PodSix.Resource import *
from PodSix.Platformer.Character import Character
from PodSix.Platformer.Portal import Portal
from PodSix.Platformer.Item import Item
from PodSix.ArrayOps import Multiply, Subtract
from PodSix.Config import config

from engine.Sprite import Sprite

def chatboxShowing(fn):
	def newfn(self, *args, **kwargs):
		if not self.chatbox.visible:
			return fn(self, *args, **kwargs)
	return newfn

class Player(Character, EventMonitor, Sprite):
	def __init__(self, game, *args, **kwargs):
		Character.__init__(self, *args, **kwargs)
		EventMonitor.__init__(self)
		self.game = game
		self.chatbox = game.hud.chatBox
		self.inventory = []
		self.portal = None
		self.hspeed = self.hspeed / config.zoom
		self.jump = self.jump / config.zoom
		self.framerate = 25
		Sprite.__init__(self, "player", ["stand.left", "stand.right", "walk.left", "walk.right", "jump.left", "jump.right"])
		for action in self.actions:
			for img in self.actions[action]:
				img.Scale(Multiply(img.Size(), config.zoom))
	
	###
	### Game events
	###
	
	def Die(self):
		sfx.PlaySound("die")
		self.game.PlayerDied()
	
	def Collide(self, who):
		Character.Collide(self, who)
		
		# TODO: check for a copy of the item instead of the actual item
		if isinstance(who, Item) and who.visible and not who in self.inventory:
			self.game.AddMessage("got" + (who.description and " " + who.description or ""), None, 2)
			# TODO: add a copy of the item instead of the actual item
			self.inventory.append(who)
			who.Hide()
			sfx.PlaySound("item")
		
		if isinstance(who, Portal):
			self.portal = who
	
	def Do(self):
		if self.portal:
			sfx.PlaySound("portal")
			if self.game.Teleport(self.portal):
				self.game.AddMessage("teleporting to " + self.portal.destination.split(":")[0])
	
	###
	### Concurrency related methods
	###
	
	def Draw(self):
		Sprite.Draw(self)
		#gfx.DrawRect(self.level.camera.TranslateRectangle(self.rectangle), [255, 200, 200], 1)
	
	def Update(self):
		Character.Update(self)
		if self.velocity[1] > 3.0 / config.zoom:
			self.Die()
		self.portal = None
	
	def Pump(self):
		Character.Pump(self)
		EventMonitor.Pump(self)
	
	###
	### Input events etc.
	###
	
	# key events
	@chatboxShowing
	def KeyDown_right(self, e):
		self.WalkRight()
	
	@chatboxShowing
	def KeyDown_left(self, e):
		self.WalkLeft()
	
	@chatboxShowing
	def KeyUp_right(self, e):
		self.StopRight()
	
	@chatboxShowing
	def KeyUp_left(self, e):
		self.StopLeft()
	
	@chatboxShowing
	def KeyDown_up(self, e):
		if self.platform:
			sfx.PlaySound("jump")
		self.Jump()
	
	@chatboxShowing
	def KeyDown_return(self, e):
		self.Do()
	
	# joystick buttons
	def JoystickDown_right(self, e):
		self.KeyDown_right(e)
	
	def JoystickDown_left(self, e):
		self.KeyDown_left(e)
	
	def JoystickUp_right(self, e):
		self.KeyUp_right(e)
	
	def JoystickUp_left(self, e):
		self.KeyUp_left(e)
	
	def JoystickDown_up(self, e):
		self.KeyDown_up(e)
	
	def JoyButtonDown(self, e):
		self.KeyDown_return(e)

