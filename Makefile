.PHONY: start-postgres stop-postgres
POSTGRES_PASSWORD ?= postgres
POSTGRES_USER ?= postgres
start-postgres:
	docker run -p 5432:5432 --name test-postgres -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -e POSTGRES_USER=${POSTGRES_USER} -d postgres:14.3

stop-postgres:
	docker stop test-postgres && docker rm test-postgres
