from PodSix.GUI.TimedText import TimedText

class Notification(TimedText):
	messagecount = 0
	messagetop = 0
	spacing = 0.06
	
	def __init__(self, game, *args, **kwargs):
		self.game = game
		kwargs['position'] = {"centerx": 0.5, "top": 0.05 + Notification.messagetop}
		if not kwargs.has_key('time') or not kwargs['time']:
			kwargs['time'] = 0.2
		kwargs['color'] = [150, 150, 150]
		if kwargs.has_key('callback') and kwargs['callback']:
			self.callback = kwargs['callback']
		del kwargs['callback']
		TimedText.__init__(self, *args, **kwargs)
		Notification.messagecount += 1
		Notification.messagetop += self.spacing
	
	def TimeOut(self):
		Notification.messagecount -= 1
		if Notification.messagecount == 0:
			Notification.messagetop = 0
		self.game.RemoveMessage(self)
		if hasattr(self, 'callback'):
			self.callback()
