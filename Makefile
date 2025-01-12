include makefiles/help.mk
include makefiles/docker.mk
include makefiles/docker-ci.mk
include makefiles/poetry.mk
include makefiles/alembic.mk

DB_APP=api

install: ## Install the dev environment(mainly for local development)
	git submodule update --init --recursive  # ensure submodule is pull to latest
	# install asdf plugins
	asdf plugin add pre-commit
	asdf plugin add python
	asdf plugin add poetry
	# install asdf packages
	asdf install

slack-server: requirements.txt ## start slack server
	docker compose up --build server-slack

discord-server: requirements.txt ## start discord server
	docker compose up --build server-discord

debug-server: requirements.txt ## start app server with debug mode
	docker compose up --build server-debug

api-server: requirements.txt ## start app server
	docker compose up --build api

test: docker-test  ## Unit test, alias for docker-test

test-int: docker-test-int  ## Intergation test, alias for docker-test-init
