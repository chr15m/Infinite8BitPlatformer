#/bin/sh

name=$(pwd | xargs basename)
/System/Library/Frameworks/Python.framework/Versions/2.5/Extras/bin/py2applet Infinite8bitPlatformer.py resources/
#py2applet $name.py
#cp -R resources/ $name.app/Contents/Resources/resources
cp resources/icon.icns $name.app/Contents/Resources/
