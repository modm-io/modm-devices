
LBUILD = ../library-builder/scripts/lbuild

discover:
	$(LBUILD)-discover -c"test/project.lb" --discover=repository:options
	$(LBUILD)-discover -c"test/project.lb" --discover=modules -D":target=stm32f303k6"
	$(LBUILD)-discover -c"test/project.lb" --discover=module:options -D":target=stm32f303k6"

build:
	$(LBUILD) --outpath="test/" -c"test/project.lb"

clean:
	$(RM) -r test/src

profile:
	python3 -m cProfile -s cumulative $(LBUILD)-discover -c"test/project.lb" --discover=repository:options

.PHONY : discover build profile clean
