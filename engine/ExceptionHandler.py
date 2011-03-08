from os import path
import sys
import traceback
import cStringIO
import webbrowser
import base64
import urllib
import gzip
from pprint import pformat

from PodSix.Resource import *
from PodSix.Game import Game

from engine.NetMonitor import NetErrorException, NetDisconnectionException, NetBadVersionException
from engine.BuildFile import buildfile

class ExceptionHandler(Game, EventMonitor):
	def __init__(self):
		# before anything, fetch the exception that was thrown and it's value
		exctype, value = sys.exc_info()[:2]
		# now print the traceback out as per usual
		traceback.print_exc()
		#sfx.LoadSound('splash')
		#sfx.PlaySound('splash')
		self.bgColor = (255, 255, 255)
		gfx.Caption('Infinite 8-bit Platformer')
		gfx.SetSize([640, 200])
		gfx.LoadFont("freaky_fonts_ca", 16.0 / gfx.width)
		
		# by default don't open a browser window
		self.destination = None
		
		# if this is not a known exception then we want the crashdump
		if not exctype in [NetErrorException, NetDisconnectionException, NetBadVersionException]:
			value = "Argh, Infinite 8-Bit Platformer crashed! Click here to send us a crash-report so we can fix the bug. Thank you!"
			# now collect the value of the traceback into our file like object
			catcherror = cStringIO.StringIO()
			# prepare a zipfile filter to push everything through
			zipout = gzip.GzipFile(fileobj=catcherror, mode="w")
			# wrap the error catcher in gzip
			traceback.print_exc(file=zipout)
			# append the buildfile information to the zip we are sending
			zipout.write("\n\nBuild info JSON:\n" + pformat(buildfile.GetInfo()))
			zipout.close()
			# get the result out
			ziptrace = catcherror.getvalue()
			self.destination = "http://infiniteplatformer.com/feedback?" + urllib.urlencode({"trace": base64.b64encode(ziptrace)})
		
		if exctype == NetBadVersionException:
			self.message = gfx.WrapText("A new version of the game is available! Click here to visit http://infiniteplatformer.com/download to get the latest version.", 0.8)
			self.destination = "http://infiniteplatformer.com/download"
			self.face = pygame.image.load(path.join(*["resources", "icons", "happy-invert.png"]))
		else:
			self.message = gfx.WrapText(str(value), 0.8)
			self.face = pygame.image.load(path.join(*["resources", "icons", "sad-invert.png"]))
		
		Game.__init__(self)
		EventMonitor.__init__(self)
	
	def Pump(self):
		Game.Pump(self)
		EventMonitor.Pump(self)
	
	def Run(self):
		gfx.screen.blit(self.face, [16, 16])
		for l in range(len(self.message)):
			gfx.DrawText(self.message[l], pos={"left": 0.1, "top": 0.05 + 0.05 * l}, color=[255, 255, 255])
		Game.Run(self)
		gfx.Flip()
	
	def KeyDown(self, e):
		self.Quit()
	
	def MouseDown(self, e):
		if self.destination:
			webbrowser.open(self.destination)
		self.Quit()

