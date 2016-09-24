
LBUILD = ../library-builder/scripts/lbuild

REPOS = -r"source/repo.lb"

discover:
	$(LBUILD)-discover $(REPOS) --discover=repository:options

profile:
	python3 -m cProfile -s cumulative $(LBUILD)-discover $(REPOS) --discover=repository:options
