lint:
	black --check .
	flake8
	mypy --strict pongy
	pylint pongy
test:
	pytest --cov
release:
	pre-commit run --all-files
	poetry version $(version)
	git commit -am "Release v$$(poetry version -s)"
	git tag -a "v$$(poetry version -s)" -m "v$$(poetry version -s)"
	git push
	git push --tags
	poetry build
	poetry publish
