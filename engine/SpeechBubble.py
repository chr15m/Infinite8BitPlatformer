from PodSix.GUI.TimedText import TimedText
from PodSix.Resource import *

class SpeechBubble(TimedText):
	def __init__(self, player, text):
		self.player = player
		
		kwargs = {"time": 3}
		kwargs['position'] = {"centerx": 0.5, "top": 0.5}
		if not kwargs.has_key('time') or not kwargs['time']:
			kwargs['time'] = 0.2
		kwargs['color'] = [75, 75, 75]
		kwargs['font'] = 'speech'
		
		self.black = [0, 0, 0]
		self.white = [255, 255, 255, 150]
		
		TimedText.__init__(self, text, **kwargs)
	
	def Draw(self):
		if self.visible:
			if not hasattr(self, "rect"):
				TimedText.Draw(self)
			# fix new pos relative to player
			# TODO: make speech bubbles avoid players and other speech bubbles on a 'rope' from the player
			r = self.player.level.camera.TranslateRectangle(self.player.rectangle)
			self.pos = {"centerx": r.CenterX() / gfx.width, "bottom": (r.Top() - 4) / gfx.width}
			# draw a nice box
			gfx.DrawRect([self.rect.left - 3, self.rect.top - 3, self.rect.width + 7, self.rect.height + 7], self.white, 0)
			gfx.DrawLines([(self.rect.left - 3, self.rect.top - 4), (self.rect.right + 4, self.rect.top - 4)], self.black, False)
			gfx.DrawLines([(self.rect.left - 3, self.rect.bottom + 4), (self.rect.right + 4, self.rect.bottom + 4)], self.black, False)
			gfx.DrawLines([(self.rect.left - 4, self.rect.top - 3), (self.rect.left - 4, self.rect.bottom + 4)], self.black, False)
			gfx.DrawLines([(self.rect.right + 4, self.rect.top - 3), (self.rect.right + 4, self.rect.bottom + 4)], self.black, False)
			TimedText.Draw(self)
		
	def Update(self):
		TimedText.Update(self)

	def TimeOut(self):
		if self.player.sb == self:
			self.player.sb = None
		self.player.Remove(self)

