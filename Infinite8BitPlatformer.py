import os
from sys import platform, path, argv

if platform == "win32" and (path[0].endswith(".exe") or path[0].endswith(".zip")):
	os.chdir(os.path.dirname(path[0]))
else:
	os.chdir(path[0])

def debug(msg):
	if "debug" in argv:
		print msg

debug("before buildfile")

# this has to happen before psyco import because of some kind of bug
from engine.BuildFile import buildfile

debug("after buildfile")

try:
	import psyco           # psyco does not exist on 64 bit platforms
	psyco.full()
except ImportError:
	print "Psyco not available"
except ValueError:
	print "No psyco due to import problems"
except WindowsError:
	print "No psyco in Windows binary"

debug("after psyco")

import PodSix
PodSix.engine = "pygame"
from PodSix.Resource import *

debug("after podsix imports")

from engine.Core import Core
from engine.ExceptionHandler import ExceptionHandler

debug("after all imports")

try:
	if platform == "win32":
		gfx.SetIcon(os.path.join("resources", "icon.gif"))
	
	from PodSix.Config import config
	config.debug = debug
	config.debugmode = "debug" in argv
	config.SetFilename("Infinite8BitPlatformer.cfg")
	
	c = Core((len(argv) >= 2 and not argv[1] in ["profile", "debug"]) and argv[1] or "i8bp.infiniteplatformer.com")
	if "profile" in argv:
		import cProfile as profile
		profile.run('c.Launch()')
	else:
		c.Launch()
	# save the config file on exit
	config.Save()
except:
	ExceptionHandler().Launch()

