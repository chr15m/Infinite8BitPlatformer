XCFS=$(wildcard *.xcf)
PNGS=$(XCFS:.xcf=.png)

all: $(PNGS)

%.png: %.xcf
	convert $< -scale 32 -background none -layers merge $@
	convert $< -scale 32 -background none -layers merge -fill black -opaque red $(@:.png=-invert.png)

clean:
	rm *.png

