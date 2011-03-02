from setuptools import setup
from sys import platform, argv
import os
from shutil import rmtree, copytree
import zipfile
try:
	from simplejson import dumps
except ImportError:
	from json import dumps

from bzrlib.branch import Branch

# get the current bzr version number
revno = Branch.open(".").revno()
app = 'Infinite8BitPlatformer'

# remove the build and dist directories
def clean():
	print "Removing build and dist directories"
	for d in ["build", "dist"]:
		if os.path.isdir(d):
			rmtree(d)

clean()

# the default os string and extension for each platform
platforms = {
	"darwin": ("osx", ".app", "dist/Infinite8BitPlatformer.app/Contents/Resources"),
	"win32": ("windows", "", "dist"),
	"linux2": ("linux", "", "dist"),
}

# more convenient representation of the platform config
config = {
	"platform": platform,
	"os": platforms[platform][0],
	"extension": platforms[platform][1],
	"resources": platforms[platform][2],
	"revno": revno,
	}

# output the build.json config file for this build
print "Writing build.json file"
version_file = file(os.path.join("resources", "build.json"), "w")
version_file.write(dumps(config))
version_file.close()

### PLATFORM SPECIFIC SECTION ###

# mac osx
if platform == "darwin":
	# add mac specific options
	options = {
		'includes': ['simplejson', 'pygame'],
		'resources': ['resources',],
		'argv_emulation': True,
		'iconfile': 'resources/icon.icns',
		'semi_standalone': False,
	}

	# force the py2app build
	argv.insert(1, "py2app")
	
	# setup for mac .app (does the actual build)
	setup(
		setup_requires=['py2app'],
		app=[app + ".py"],
		options={'py2app': options},
	)
elif platform == "win32":
	import py2exe
	
	# hack to include simplejson egg in the build
	import pkg_resources
	eggs = pkg_resources.require("simplejson")
	from setuptools.archive_util import unpack_archive
	for egg in eggs:
		if os.path.isdir(egg.location):
			copytree(egg.location, ".")
		else:
			unpack_archive(egg.location, ".")
			rmtree("EGG-INFO")
	
	# windows specific options
	options = {
		"script": app + ".py",
		"icon_resources": [(1, os.path.join("resources", "main.ico"))],
	}
	resources = ['resources',]
	
	# force the py2exe build
	argv.insert(1, "py2exe")
	
	# setup for windows .exe (does the actual build)
	setup(
		setup_requires = ['py2exe'],
		windows=[options],
	)
	
	# manually copy resources as I couldn't get it to happen with py2exe
	for r in resources:
		print 'Copying resource "%s"' % r
		copytree(r, os.path.join("dist", r))
	
	# get rid of simplejson directory
	rmtree("simplejson")
elif platform == "linux2":
	os.mkdir(platforms[platform][2])
	copytree("resources", os.path.join("dist", "resources"))

### PLATFORM SECTION DONE ###

# zip up our app to the correctly named zipfile
def recursive_zip(zipf, directory, root=None):
	if not root:
		root = os.path.basename(directory)
	list = os.listdir(directory)
	for file in list:
		realpath = os.path.join(directory, file)
		arcpath = os.path.join(root, file)
		print "Zipping:", arcpath
		if os.path.isfile(realpath):
			zipf.write(realpath, arcpath)
		elif os.path.isdir(realpath):
			recursive_zip(zipf, realpath, arcpath)

outfilename = "%s-%d-%s%s.zip" % (app, revno, config["os"], config["extension"])
zipout = zipfile.ZipFile(outfilename, "w")
recursive_zip(zipout, os.path.join("dist", platform == "darwin" and app + config["extension"] or ""))
zipout.close()

# clean up afterwards
clean()

# output the build-finished message
print "--- done ---"
print "Created %s" % outfilename
