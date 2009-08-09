import os
from sys import platform, path

import psyco
psyco.full()

if platform == "win32":
	# one level up from library.zip
	os.chdir(os.sep.join(path[0].split(os.sep)[:-1]))
else:
	os.chdir(path[0])

import PodSix
PodSix.engine = "pygame"
from PodSix.Resource import *
gfx.SetIcon(os.path.join("resources", "icon.gif"))

#from PodSix.SplashScreen import SplashScreen
#s = SplashScreen()
#s.Launch()

from engine.Core import Core
c = Core()

import cProfile as profile
profile.run('c.Launch()')
#c.Launch()

