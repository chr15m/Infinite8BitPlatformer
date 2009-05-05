import os
from sys import platform, path

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
c.Launch()

