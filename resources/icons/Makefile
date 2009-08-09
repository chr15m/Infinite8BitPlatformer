XCFS=$(wildcard *.xcf)
GIFS=$(XCFS:.xcf=.gif)

all: $(GIFS)

%.gif: %.xcf
	convert $< $@

clean:
	rm *.gif

