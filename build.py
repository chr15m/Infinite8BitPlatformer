from setuptools import setup
from sys import platform, argv
import os
from shutil import rmtree, copytree
import zipfile
# TODO: do we really need to still support simplejson?
# if OSX builds for 2.6 let's ditch it
using_simplejson = False
try:
	from simplejson import dumps
	using_simplejson = True
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
		'includes': ['pygame'],
		'resources': ['resources',],
		'argv_emulation': True,
		'iconfile': 'resources/icon.icns',
		'semi_standalone': False,
	}
	if using_simplejson:
		options['includes'].insert(0, 'simplejson')
	
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
	import pygame
	import glob
	import sys
	
	# hack to patch in win32com support
	# http://www.py2exe.org/index.cgi/win32com.shell
	# ...
	# ModuleFinder can't handle runtime changes to __path__, but win32com uses them
	try:
	    # py2exe 0.6.4 introduced a replacement modulefinder.
	    # This means we have to add package paths there, not to the built-in
	    # one.  If this new modulefinder gets integrated into Python, then
	    # we might be able to revert this some day.
	    # if this doesn't work, try import modulefinder
	    try:
		import py2exe.mf as modulefinder
	    except ImportError:
		import modulefinder
	    import win32com
	    for p in win32com.__path__[1:]:
		modulefinder.AddPackagePath("win32com", p)
	    for extra in ["win32com.shell"]: #,"win32com.mapi"
		__import__(extra)
		m = sys.modules[extra]
		for p in m.__path__[1:]:
		    modulefinder.AddPackagePath(extra, p)
	except ImportError:
	    # no build path setup, no worries.
	    pass

	# hack to include simplejson egg in the build
	if using_simplejson:
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
	
	# horrible monkey patch to make sdl mixer include work (say what?)
	# http://www.python-forum.org/pythonforum/viewtopic.php?f=3&t=19455&start=0
	origIsSystemDLL = py2exe.build_exe.isSystemDLL
	def isSystemDLL(pathname):
	        if os.path.basename(pathname).lower() in ("libogg-0.dll", "sdl_ttf.dll"):
	                return 0
	        return origIsSystemDLL(pathname)
	py2exe.build_exe.isSystemDLL = isSystemDLL
	
	# stuff for shrinking the final binary
	# http://www.moviepartners.com/blog/2009/03/20/making-py2exe-play-nice-with-pygame/
	INCLUDE_STUFF = ['encodings', "encodings.latin_1", "pygame", "win32com.shell"]
	
	MODULE_EXCLUDES =[
		'email',
		'AppKit',
		'Foundation',
		'bdb',
		'difflib',
		'tcl',
		'Tkinter',
		'Tkconstants',
		'curses',
		'distutils',
		'setuptools',
		#'urllib',
		#'urllib2',
		#'urlparse',
		#'BaseHTTPServer',
		'_LWPCookieJar',
		'_MozillaCookieJar',
		'ftplib',
		'gopherlib',
		#'_ssl',
		'htmllib',
		'httplib',
		#'mimetools',
		'mimetypes',
		#'rfc822',
		'tty',
		#'webbrowser',
		#'socket',
		#'hashlib',
		#'base64',
		'compiler',
		'pydoc',
		'bzrlib',
	]
	
	# the rest of this stuff is from the original
	
	# force the py2exe build
	argv.insert(1, "py2exe")
	
	# setup for windows .exe (does the actual build)
	setup(
		setup_requires = ['py2exe'],
		windows=[options],
		options = {
			"py2exe": {
				"optimize": 2,
				"includes": INCLUDE_STUFF,
				"compressed": 1,
				#"ascii": 1,
				# whether all library files should be bundled into the exe
				"bundle_files": 2,
				"ignores": ['tcl', 'AppKit', 'Numeric', 'Foundation'],
				"excludes": MODULE_EXCLUDES
			}
		},
		zipfile = None,
	)
	
	# manually copy resources as I couldn't get it to happen with py2exe
	for r in resources:
		print 'Copying resource "%s"' % r
		copytree(r, os.path.join("dist", r))
	
	if using_simplejson:
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
