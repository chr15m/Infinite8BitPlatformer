from distutils.core import setup
from sys import argv
from os import path, listdir, mkdir, chdir
import shutil
import py2exe
from os import getcwd

# delete the old build and dist directories for a clean start
for d in ["build", "dist"]:
	if path.isdir(d):
		shutil.rmtree(d)

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
)

# hand copy the resources directory
shutil.copytree("resources", path.join("dist", "resources"))
