import os
from sys import platform, path, argv

try:
	import psyco           # psyco does not exist on 64 bit platforms
	psyco.full()
except ImportError:
	pass

if platform == "win32":
	# one level up from library.zip
	os.chdir(os.sep.join(path[0].split(os.sep)[:-1]))
else:
	os.chdir(path[0])

import PodSix
PodSix.engine = "pygame"
from PodSix.Resource import *
gfx.SetIcon(os.path.join("resources", "icon.gif"))

#from PodSix.Config import config
#config.SetFilename("Infinite8BitPlatformer.cfg")

#from PodSix.SplashScreen import SplashScreen
#s = SplashScreen()
#s.Launch()

from engine.Core import Core
c = Core()

if len(argv) == 2 and argv[1] == "profile":
	import cProfile as profile
	profile.run('c.Launch()')
else:
	c.Launch()

# save the config file on exit
#config.Save()
