from os import path
from sys import platform

import PodSix
PodSix.engine = "pygame"
from PodSix.Resource import *
gfx.SetIcon(path.join("resources", "icon.gif"))

from PodSix.SplashScreen import SplashScreen
s = SplashScreen()
s.Launch()

from Core import Core
c = Core()
c.Launch()

