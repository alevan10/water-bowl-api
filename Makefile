.PHONY: start-postgres stop-postgres black lint
POSTGRES_PASSWORD ?= postgres
POSTGRES_USER ?= postgres
start-postgres:
	docker run -p 5432:5432 --rm --name test-postgres -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -e POSTGRES_USER=${POSTGRES_USER} -d postgres:14.3

stop-postgres:
	docker stop test-postgres

black:
	python -m black .

lint:
	pylint -E -d C0301 src/waterbowl-api tests
