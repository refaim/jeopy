.PHONY: all clean

all: jeopy

clean:
	$(RM) -r build

jeopy:
	python build.py
