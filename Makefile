
test:
	@python3 -W ignore::DeprecationWarning -m unittest discover -p *test.py

dist:
	@rm -rf dist build
	@python3 setup.py sdist bdist_wheel

install:
	@python3 setup.py install --record uninstall.txt

install-user:
	@python3 setup.py install --user

upload: dist
	@twine upload --skip-existing dist/*

.PHONY : test dist install install-user upload
