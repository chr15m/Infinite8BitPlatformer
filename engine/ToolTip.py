from PodSix.Resource import *
from PodSix.GUI.Widget import Widget
from PodSix.GUI.Button import Button

class ToolTip(Widget):
	"""
	Singleton for tooltip widget help.
	"""
	def __init__(self, font="default", color=[0, 0, 0]):
		Widget.__init__(self)
		self.font = font
		self.color = color
		self.bg = (255, 255, 255)
		self.widget = None
		# should be always on top of everything
		self.priority = 100
		self.pos = {"centerx": 0.5, "centery": 0.05}
		self.rect = None
		Button.tooltip = self
	
	def __call__(self, widget):
		"""
		set new widget
		"""
		self.widget = hasattr(widget, "help_text") and widget or None
	
	def Draw(self):
		if self.widget:
			pos = gfx.GetMouse()
			if not self.widget.InRect(pos):
				self.widget = None
				self.rect = None
			else:
				self.rect = gfx.DrawText(self.widget.help_text, self.pos, self.color, self.font)
				gfx.DrawRect([self.rect.left - 3, self.rect.top - 3, self.rect.width + 7, self.rect.height + 7], self.bg, 0)
				gfx.DrawLines([(self.rect.left - 3, self.rect.top - 4), (self.rect.right + 4, self.rect.top - 4)], self.color, False)
				gfx.DrawLines([(self.rect.left - 3, self.rect.bottom + 4), (self.rect.right + 4, self.rect.bottom + 4)], self.color, False)
				gfx.DrawLines([(self.rect.left - 4, self.rect.top - 3), (self.rect.left - 4, self.rect.bottom + 4)], self.color, False)
				gfx.DrawLines([(self.rect.right + 4, self.rect.top - 3), (self.rect.right + 4, self.rect.bottom + 4)], self.color, False)
				self.rect = gfx.DrawText(self.widget.help_text, self.pos, self.color, self.font)

tooltip = ToolTip()
