#/bin/sh

name=$(pwd | xargs basename)
py2applet $name.py
cp -R resources/ $name.app/Contents/Resources/resources
cp resources/icon.icns $name.app/Contents/Resources/
