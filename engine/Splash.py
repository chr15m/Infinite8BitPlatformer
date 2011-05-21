from os import path
from time import time

from PodSix.Resource import *
from PodSix.Concurrent import Concurrent
from PodSix.Timer import Timer
from PodSix.GUI.Graphic import Graphic

class Splash(Concurrent):
	"""
		Splash screen.
	"""
	def __init__(self, game):
		sfx.LoadSound("coinup-splash-1")
		sfx.LoadSound("coinup-splash-2")
		self.game = game
		Concurrent.__init__(self)
		self.Add(Graphic(Image(path.join("resources", "title.png")), [216, 48]))
		self.Add(Graphic(Image(path.join("resources", "alpha.png")), [697, 103]))
		self.Add(Timer(1.0, True, self.Triggered))
		self.black = (0, 0, 0)
	
	def Draw(self):
		gfx.SetBackgroundColor(self.black)
		Concurrent.Draw(self)
	
	def Triggered(self, trigger):
		if trigger == 0:
			self.Add(Graphic(Image(path.join("resources", "bychris.png")), [292, 214]))
			sfx.PlaySound("coinup-splash-1")
		elif trigger == 1:
			self.Add(Graphic(Image(path.join("resources", "podsix.png")), [236, 236]))
			sfx.PlaySound("coinup-splash-1")
		elif trigger == 2:
			self.Add(Graphic(Image(path.join("resources", "scout.png")), [664, 400]))
			sfx.PlaySound("coinup-splash-2")
		elif trigger == 4:
			self.game.StartGame()

