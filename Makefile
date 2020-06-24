
test:
	@python3 -W ignore::DeprecationWarning -m unittest discover -p *test.py

.PHONY : test
