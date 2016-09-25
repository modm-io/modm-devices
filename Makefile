
LBUILD = ../library-builder/scripts/lbuild

REPOS = -r"source/repo.lb"

discover:
	$(LBUILD)-discover $(REPOS) --discover=repository:options

discover:
	$(LBUILD)-discover $(REPOS) --discover=modules -D":target=stm32f303k6"

profile:
	python3 -m cProfile -s cumulative $(LBUILD)-discover $(REPOS) --discover=repository:options
