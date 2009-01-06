#/bin/sh

py2applet MinimalistPlatformer.py
cp -R resources/ MinimalistPlatformer.app/Contents/Resources/resources
cp resources/icon.icns MinimalistPlatformer.app/Contents/Resources/
