XCFS=$(wildcard *.xcf)
PNGS=$(XCFS:.xcf=.png)

all: $(PNGS)

%.png: %.xcf
	convert $< -scale 32 -composite $@
	convert $< -scale 32 -composite -fill black -opaque red $(@:.png=-invert.png)

clean:
	rm *.png

