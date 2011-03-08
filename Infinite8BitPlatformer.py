import os
from sys import platform, path, argv

if platform == "win32" and "library.zip" in path[0]:
	# one level up from library.zip
	os.chdir(os.sep.join(path[0].split(os.sep)[:-1]))
else:
	os.chdir(path[0])

# this has to happen before psyco import because of some kind of bug
from engine.BuildFile import buildfile

try:
	import psyco           # psyco does not exist on 64 bit platforms
	psyco.full()
except ImportError:
	print "Psyco not available"
	pass

import PodSix
PodSix.engine = "pygame"
from PodSix.Resource import *

#from PodSix.SplashScreen import SplashScreen
#s = SplashScreen()
#s.Launch()

from engine.Core import Core
from engine.ExceptionHandler import ExceptionHandler

try:
	if platform == "win32":
		gfx.SetIcon(os.path.join("resources", "icon.gif"))
	
	from PodSix.Config import config
	config.SetFilename("Infinite8BitPlatformer.cfg")
	
	c = Core((len(argv) >= 2 and argv[1] != "profile") and argv[1] or "i8bp.infiniteplatformer.com")
	if "profile" in argv:
		import cProfile as profile
		profile.run('c.Launch()')
	else:
		c.Launch()
	# save the config file on exit
	config.Save()
except:
	ExceptionHandler().Launch()

