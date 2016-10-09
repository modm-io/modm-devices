
LBUILD = python3 ../library-builder/scripts/lbuild

discover:
	$(LBUILD) -c"test/project.lb" discover-repository
	$(LBUILD) -c"test/project.lb" -D":target=stm32f303k6" discover-modules
	$(LBUILD) -c"test/project.lb" -D":target=stm32f303k6" discover-module-options

build:
	$(LBUILD) --path="test/" -c"test/project.lb" build

clean:
	$(RM) -r test/src

profile:
	python3 -m cProfile -s cumulative $(LBUILD)-discover -c"test/project.lb" --discover=repository:options

.PHONY : discover build profile clean
