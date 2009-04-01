from PodSix.GUI.TimedText import TimedText
from PodSix.Resource import *

class Notification(TimedText):
	slots = {}
	
	def __init__(self, game, *args, **kwargs):
		self.game = game
		slot = max(Notification.slots.keys() + [0]) + 1
		top = max([Notification.slots[i].bottom for i in Notification.slots] + [0.05])
		self.bottom = top + gfx.FontHeight() * (len(args[0].split("\n")) + 1)
		
		kwargs['position'] = {"centerx": 0.5, "top": top}
		if not kwargs.has_key('time') or not kwargs['time']:
			kwargs['time'] = 0.2
		kwargs['color'] = [150, 150, 150]
		if kwargs.has_key('callback') and kwargs['callback']:
			self.callback = kwargs['callback']
		del kwargs['callback']
		
		Notification.slots[slot] = self
		self.slot = slot
		TimedText.__init__(self, *args, **kwargs)
		self.originalColor = self.color[:]
	
	def Update(self):
		self.color = [max(15, int(self.counter / self.time * x)) for x in self.originalColor]
		TimedText.Update(self)
	
	def TimeOut(self):
		del Notification.slots[self.slot]
		self.game.RemoveMessage(self)
		if hasattr(self, 'callback'):
			self.callback()
