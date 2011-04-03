import PodSix
PodSix.engine = "pygame"
from PodSix.Resource import *
from PodSix.Config import config

config.SetFilename("Infinite8BitPlatformer.cfg")
config.zoom = 5

gfx.width = 800
gfx.height = 450

from engine.BitLevel import BitLevel

n = BitLevel("24", None)

import cProfile as profile
profile.run('n.Load()')

