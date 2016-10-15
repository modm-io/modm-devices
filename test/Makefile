
LBUILD = python3 ../../library-builder/scripts/lbuild

init:
	$(LBUILD) -vv init

update:
	$(LBUILD) -vv update

discover:
	$(LBUILD) -c"project.lb" -vv discover-repository
	$(LBUILD) -c"project.lb" -D":target=stm32f303k6" discover-modules
	$(LBUILD) -c"project.lb" -D":target=stm32f303k6" discover-module-options

dependencies:
	$(LBUILD) -c"project.lb" -D":target=stm32f303k6" dependencies > dep.dot
	dot -Tpng dep.dot > dep.png
	xdg-open dep.png

build:
	$(LBUILD) --path="." -c"project.lb" build

clean:
	$(RM) -r src
	$(RM) -r lbuild_cache

profile:
	python3 -m cProfile -s cumulative $(LBUILD)-discover -c"project.lb" discover-repository

.PHONY : discover build profile clean
