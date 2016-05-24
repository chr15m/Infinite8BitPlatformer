import PodSix
PodSix.engine = "pygame"
from PodSix.Resource import *
from PodSix.Config import config
config.SetFilename("Infinite8BitPlatformer.cfg")
config.zoom = 5
from engine.BitLevel import BitLevel
b = BitLevel("1", None)
b.Load()
print b.history
