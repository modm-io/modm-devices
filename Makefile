
LBUILD = ../library-builder/scripts/lbuild

REPOS = -r"source/repo.lb"

discover:
	$(LBUILD)-discover $(REPOS) --discover=repository:options
	$(LBUILD)-discover $(REPOS) --discover=modules -D":target=stm32f303k6"
	$(LBUILD)-discover $(REPOS) --discover=module:options -D":target=stm32f303k6"

build:
	$(LBUILD) $(REPOS) --outpath="test/" -c"test/project.lb"

clean:
	$(RM) -r test/src

profile:
	python3 -m cProfile -s cumulative $(LBUILD)-discover $(REPOS) --discover=repository:options

.PHONY : discover build profile clean
