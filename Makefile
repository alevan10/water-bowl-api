.PHONY: start-postgres stop-postgres black lint isort run-local stop-local push-prod check-isort check-black
POSTGRES_PASSWORD ?= postgres
POSTGRES_USER ?= postgres
start-postgres:
	docker compose up -d postgres

stop-postgres:
	docker compose down

black:
	python -m black .

check-black:
	python -m black . --check --verbose

lint:
	pylint -E -d C0301 src/waterbowl_api tests

isort:
	isort --profile black .

check-isort:
	isort --profile black -c -v .

build:
	docker buildx build -f src/docker/Dockerfile --platform linux/amd64 --tag levan.home:5000/water-bowl-api:$(shell python version_checker.py --return-version) --load .
	docker buildx build -f src/docker/Dockerfile --platform linux/arm64 --tag levan.home:5000/water-bowl-api:$(shell python version_checker.py --return-version) --load .

run-local:
	docker compose up --build -d

stop-local:
	docker compose down

push-prod: build
	docker push levan.home:5000/water-bowl-api:$(shell python version_checker.py --return-version)
