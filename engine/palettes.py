try:
	from json import dumps, loads
except ImportError:
	from simplejson import dumps, loads
from os import listdir, path

from pygame import image

# base path to the palette files
basepath = path.join("resources", "palettes")

# source json file
jsonfile = path.join(basepath, "palettes.json")

# all of the palettes in the game (pallettes.all)
all = None

if path.isfile(jsonfile):
	all = loads(file(jsonfile).read())
else:
	# make the base palette
	base = []
	
	max = 0xFFFFFF
	for x in range(255):
		val = int(round(x / 254.0 * max))
		r = 0x0000FF & val
		g = (0x00FF00 & val) >> 8
		b = (0xFF0000 & val) >> 16
		base.append((r, g, b))
	
	def dist(c1, c2):
		return sum([pow(c2[x] - c1[x], 2) for x in range(3)])
	
	# reference palettes which index into the same as the 256 color one
	all = {}
	
	# for every palette file
	pfiles = [f for f in listdir(basepath) if f[-4:] == ".png"]
	for f in pfiles:
		# extract the colours from the image
		pf = image.load(path.join(basepath, f))
		name = f[:-4]
		
		# set up the reference palette
		all[name] = [(255, 0, 255)]
		
		# build a colourmap from the pixels in the image
		cmap = []
		for x in range(pf.get_width()):
			for y in range(pf.get_height()):
				cmap.append(pf.get_at((x, y))[:3])
		
		# loop through our base palette finding the
		# closest color in our reference palette
		for c in base:
			cmap.sort(lambda a,b: cmp(dist(c, a), dist(c, b)))
			all[name].append(cmap[0])
	
	file(jsonfile, "w+").write(dumps(all))

