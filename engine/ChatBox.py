from PodSix.Resource import *
from PodSix.GUI.TextInput import TextInput
from PodSix.Rectangle import Rectangle

class ChatBox(TextInput):
	def __init__(self, parent):
		self.parent = parent
		# special keys we want to ignore
		self.specials = range(0, 10) + range(11, 32) + range(127, 160) + range(0x111, 0x211)
		# last mouse position
		self.lastPos = [0, 0]
		# whether to draw this or not
		self.visible = False
		# history of commands we have typed
		self.history = []
		
		TextInput.__init__(self, {"left": 0.01, "bottom": 0.55}, 0.8, "/help", dict([(x, chr(x)) for x in range(97, 122)]), font="chat")
		self.chatIcon = Image("resources/icons/chat.png")
		# remember the drawn rectangle
		self.visible = True
		self.Draw()
		self.visible = False
		self.oldRect = self.rect
		self.oldRect[0] -= 4
		self.oldRect[1] -= 4
		self.oldRect[2] += 8
		self.oldRect[3] += 8
		self.oldRect = Rectangle(self.oldRect)
		# remember the original position
		self.oldPos = self.pos
		self.oldText = ""
		# what to run when enter is pressed
		self.callback = None
	
	def Update(self):
		if self.visible:
			TextInput.Update(self)
	
	def Draw(self):
		if self.visible:
			if self.rect:
				gfx.DrawRect([self.rect.left - 3, self.rect.top - 3, self.rect.width + 7, self.rect.height + 7], [255, 255, 255], 0)
			TextInput.Draw(self)
		else:
			gfx.BlitImage(self.chatIcon, position=(8, gfx.height - 36))
	
	def ShowText(self, text, callback=None):
		if not self.oldText:
			self.oldText = self.text
		self.text = text
		self.visible = True
		self.callback = callback
	
	def RevertText(self):
		if self.oldText:
			self.text = self.oldText
			self.oldText = ""
		self.visible = False
		self.callback = None
	
	def KeyDown(self, e):
		if self.visible:
			self.Draw()
			#print e.key
			#print e
			if self.textWidth < self.width * gfx.width  - self.letterWidth and not e.key in self.specials:
				self.text += e.unicode
			elif e.key == 13 and self.callback:
				self.callback(self.text)
			self.triggered = True
	
	def MouseMove(self, e):
		inNew = self.oldRect.PointInRect(e.pos)
		inOld = self.oldRect.PointInRect(self.lastPos)
		# mouse over
		if inNew and not inOld:
			self.visible = True
		# mouse out
		elif inOld and not inNew:
			self.visible = False
		self.lastPos = e.pos[:]

