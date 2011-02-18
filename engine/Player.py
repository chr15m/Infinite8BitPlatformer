from PodSix.Resource import *
from PodSix.Platformer.Character import Character
from PodSix.Platformer.Portal import Portal
from PodSix.Platformer.Item import Item
from PodSix.ArrayOps import Multiply, Subtract
from PodSix.Config import config
from PodSix.Concurrent import Concurrent
from PodSix.GUI.Label import Label

from PodSixNet.Connection import ConnectionListener

from engine.Sprite import Sprite
from engine.SpeechBubble import SpeechBubble

import math
import pygame
import pygame.gfxdraw

def chatboxShowing(fn):
	def newfn(self, *args, **kwargs):
		if not self.chatbox.visible:
			return fn(self, *args, **kwargs)
	return newfn

class Player(Character, EventMonitor, Sprite, ConnectionListener):
	def __init__(self, game, playerid, *args, **kwargs):
		Character.__init__(self, rectangle=[0, 0, 11.0 / gfx.width, 12.0 / gfx.width])
		EventMonitor.__init__(self)
		self.playerid = playerid
		self.game = game
		self.chatbox = game.hud.chatBox
		self.sb = None
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
		if self.game.player == self:
			self.game.PlayerDied()
	
	def Collide(self, who):
		Character.Collide(self, who)
		# TODO: check for a copy of the item instead of the actual item
		if isinstance(who, Item) and who.visible and not who in self.inventory:
			self.game.AddMessage("got" + (who.description and " " + who.description or ""), None, 2)
			# TODO: add a copy of the item instead of the actual item
			self.Collect(who)
			if self.game.player == self:
				self.game.net.SendWithID({"action": "item", "objectid": who.id})
		
		if isinstance(who, Portal):
			self.portal = who
	
	def Do(self):
		if self.portal:
			sfx.PlaySound("portal")
			if self.game.Teleport(self.portal):
				self.game.AddMessage("teleporting...", time=2.0)
	
	def HitPlatform(self, platform):
		# skip the first hitplatform of the game
		if self.game.net.playerID and self.game.player == self:
			self.SendCurrentMove()
	
	def Collect(self, item, counter=30):
		self.inventory.append(item)
		item.Hide(counter)
		sfx.PlaySound("item")
	
	###
	### Concurrency related methods
	###
	
	def Draw(self):
		Sprite.Draw(self)
		Concurrent.Draw(self)
		#gfx.DrawRect(self.level.camera.TranslateRectangle(self.rectangle), [255, 200, 200], 1)
	
	def Update(self):
		Character.Update(self)
		if self.velocity[1] > 3.0 / config.zoom:
			self.Die()
		self.portal = None
	
	def Pump(self):
		ConnectionListener.Pump(self)
		Character.Pump(self)
		# network players ignore events (keypresses, joysticks etc.)
		if not self.playerid:
			EventMonitor.Pump(self)
	###
	### Wrapper method
	###
	
	def Chat(self, text):
		self.Say(text)
		self.SendChat(text)
	
	def Say(self, text):
		t = "\n".join(gfx.WrapText(text, 0.25))
		if self.sb:
			self.sb.visible = False
		self.sb = SpeechBubble(self, t)
		self.Add(self.sb)
	
	###
	### Network stuff
	###
	
	def SendMove(self, **move):
		move.update({"action": "move", "center": self.rectangle.Center(), "velocity": self.velocity})
		self.game.net.SendWithID(move)
	
	def SendCurrentMove(self):
		self.SendMove(move=self.lastmove)
	
	def Network_move(self, data):
		if data['id'] == self.playerid:
			#print "Player move:", self.playerid, data
			self.rectangle.Center(data['center'])
			self.velocity = data['velocity']
			if data['move'] in ["WalkRight", "WalkLeft", "StopRight", "StopLeft", "Jump"]:
				# force the animation update
				getattr(self, data['move'])(force=True)
	
	def SendChat(self, text):
		    self.game.net.SendWithID({"action": "chat", "message":text})
	
	def Network_chat(self, data):
		if data['id'] == self.playerid:
			self.Say(data["message"])
	
	def Network_item(self, data):
		print "collect item:", data
		if data['id'] == self.playerid:
			self.Collect(self.game.CurrentLevel().PropFromId(data['objectid']), counter=(30 - (int(data['servertime']) - int(data['collected']))))
	
	###
	### Input events etc.
	###
	
	# key events
	@chatboxShowing
	def KeyDown_right(self, e):
		self.WalkRight()
		self.SendMove(move="WalkRight")
	
	@chatboxShowing
	def KeyDown_left(self, e):
		self.WalkLeft()
		self.SendMove(move="WalkLeft")
	
	@chatboxShowing
	def KeyUp_right(self, e):
		self.StopRight()
		self.SendMove(move="StopRight")
	
	@chatboxShowing
	def KeyUp_left(self, e):
		self.StopLeft()
		self.SendMove(move="StopLeft")
	
	@chatboxShowing
	def KeyDown_space(self, e):
		if self.platform:
			sfx.PlaySound("jump")
		self.Jump()
		self.SendMove(move="Jump")
	
	@chatboxShowing
	def KeyDown_up(self, e):
		if self.ClimbUp():
			self.SendMove(move="ClimbUp")
		else:
			self.KeyDown_space(e)
	
	@chatboxShowing
	def KeyUp_up(self, e):
		if self.grabbing:
			self.StopUp()
			self.SendMove(move="StopUp")
	
	@chatboxShowing
	def KeyDown_down(self, e):
		self.ClimbDown()
		self.SendMove(move="ClimbDown")
	
	@chatboxShowing
	def KeyUp_down(self, e):
		self.StopUp()
		self.SendMove(move="StopDown")
	
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

