from PodSix.ArrayOps import Multiply, Subtract
from PodSix.Resource import *

def TranslateCoordinates(rectangle, camera):
	return Multiply(Subtract(rectangle, camera.rectangle[:2] + [0, 0]), gfx.width)
