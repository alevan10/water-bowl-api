.PHONY: start-postgres stop-postgres black lint isort
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

isort:
	isort **/*.py

build:
		export WATER_BOWL_API_TAG=$(shell python version_checker.py --return-version)
		docker buildx build -f src/docker/Dockerfile --platform linux/amd64 --tag levan.home:5000/water-bowl-api:${WATER_BOWL_API_TAG} --load .
		docker buildx build -f src/docker/Dockerfile --platform linux/arm64 --tag levan.home:5000/water-bowl-api:${WATER_BOWL_API_TAG} --load .

push-prod: build
		docker push levan.home:5000/water-bowl-api:$(shell python version_checker.py --return-version)
