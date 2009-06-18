from distutils.core import setup
from sys import argv
from os import path, listdir, mkdir
import shutil
import py2exe
from os import getcwd

# get the name of this directory for the project_name
project_name = path.basename(getcwd())

# extra datafiles to be copied from the resources dir
datafiles = [path.join("resources", d) for d in listdir('resources') if not ".svn" in d]

# seed the install command line with what we want
argv += ["py2exe"]
setup(
	windows = [
		{
			"script": project_name + ".py",
			"icon_resources": [(1, path.join("resources", "main.ico"))]
		}
	],
)

# also need to hand copy the extra files here
def installfile(name):
	dst = path.join('dist', 'resources')
	if not path.isdir(dst):
		print 'making dir', dst
		mkdir(dst)
	print 'copying', name, '->', dst
	if path.isdir(name):
		dst = path.join(dst, name)
		if path.isdir(dst):
			shutil.rmtree(dst)
		shutil.copytree(name, dst)
	elif path.isfile(name):
		shutil.copy(name, dst)
	else:
		print 'Warning, %s not found' % name

[installfile(data) for data in datafiles]

