#/bin/sh

# prevent destructive recurse
mv PodSix/tests /tmp/podsix-tests
# get the name of this app
name=$(pwd | xargs basename)
revno=$(bzr revno)
# do the actual build
/System/Library/Frameworks/Python.framework/Versions/2.5/Extras/bin/py2applet --iconfile="`pwd`/resources/icon.icns" Infinite8BitPlatformer.py resources/
# restore PodSix tests directory
mv /tmp/podsix-tests PodSix/tests
# copy in the icon
cp resources/icon.icns $name.app/Contents/Resources/
# zip it up
zip -r Infinite8BitPlatformer-$revno-mac.app.zip Infinite8BitPlatformer.app
