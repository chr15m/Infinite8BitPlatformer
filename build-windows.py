from distutils.core import setup
from sys import argv
from os import path, listdir, mkdir, chdir, getcwd, system
from subprocess import Popen, PIPE
import shutil

# delete the old build and dist directories for a clean start
for d in ["build", "dist"]:
	if path.isdir(d):
		shutil.rmtree(d)

# hack to include simplejson egg in the build
import pkg_resources
eggs = pkg_resources.require("simplejson")

from setuptools.archive_util import unpack_archive
for egg in eggs:
	if path.isdir(egg.location):
		shutil.copytree(egg.location, ".")
	else:
		unpack_archive(egg.location, ".")
		shutil.rmtree("EGG-INFO")

import py2exe

# get the name of this directory for the project_name
project_name = path.basename(getcwd())

# seed the install command line with what we want
argv += ["py2exe"]
setup(
	windows = [
		{
			"script": project_name + ".py",
			"icon_resources": [(1, path.join("resources", "main.ico"))],
		}
	],
	#options = {"py2exe": {"packages": ["simplejson"]}},
)

# hand copy the resources directory
shutil.copytree("resources", path.join("dist", "resources"))

revno = Popen(["bzr", "revno"], stdout=PIPE).communicate()[0].rstrip()
if path.isdir(project_name):
	shutil.rmtree(project_name)
shutil.move("dist", "%s" % project_name)
system("zip -r %s-%s-windows.zip %s" % (project_name, revno, project_name))
# get rid of crap
shutil.rmtree("build")
shutil.rmtree("simplejson")
