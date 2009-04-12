from os import path

from PodSix.Resource import *
from PodSix.Rectangle import Rectangle

def MakeFilename(name, counter):
	return path.join("resources", name + "." + str(counter) + ".png")

class Sprite:
	def __init__(self, prefix, actions):
		self.actions = {}
		for action in actions:
			self.actions[action] = self.LoadNext(prefix + "." + action, 1)
		self.animframe = 0
		self.animation = "stand.right"
	
	def LoadNext(self, name, counter):
		others = []
		if path.isfile(MakeFilename(name, counter + 1)):
			others = self.LoadNext(name, counter + 1)
		return [Image(MakeFilename(name, counter))] + others
	
	def Draw(self):
		self.animframe = (self.animframe + self.Elapsed() * self.framerate) % len(self.actions[self.animation])
		gfx.BlitImage(self.actions[self.animation][int(self.animframe)], center=self.level.camera.TranslateRectangle(self.rectangle).Center())

