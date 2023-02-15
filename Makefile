test:
	pytest --tb=short

watch-tests:
	ls test*.py | entr pytest --tb=short

black:
	black -l 86 $$(find * -name '*.py')
