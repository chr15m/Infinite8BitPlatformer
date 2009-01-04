from Core import Core
from PodSix.SplashScreen import SplashScreen
from PodSix.Resource import *

gfx.SetIcon("resources/icon.gif")

s = SplashScreen()
s.Launch()

c = Core()
c.Launch()

