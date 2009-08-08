#!/usr/bin/python

from os import mkdir, listdir, path
from shutil import copy

projectName = "MinimalistPlatformer"

destDir = projectName + ".linux"

if not path.isdir(destDir):
	mkdir(destDir)

def descend(pattern, dir, dest):
	if not ".svn" in dir and "./" + destDir != dir and not 'tests' in dir:
		print "****** descended into", dir
		for f in listdir(dir):
			if not ".svn" in f:
				if path.isdir(dir + "/" + f):
					descend(pattern, dir + "/" + f, dest)
				elif pattern in f:
					print 'copying', dir + "/" + f, 'to', dest + "/" + dir
					if not path.isdir(dest + "/" + dir):
						mkdir(dest + "/" + dir)
					copy(dir + "/" + f, dest + "/" + dir)
	else:
		print "skipping", dir

print "finding .pyc files"
descend(".pyc", ".", destDir)
print

print "finding resources"
descend("", "resources", destDir)
print

print "copying script"
copy(projectName + ".py", destDir)

