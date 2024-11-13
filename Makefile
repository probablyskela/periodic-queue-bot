APP_NAME=pqbot

# generate help info from comments, source - https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help: ## help information about make commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ${MAKEFILE_LIST} | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: build
build: ## Build pqbot:latest docker image
	@docker build -f ./deployments/Dockerfile . -t ${APP_NAME}
	@docker tag ${APP_NAME} ${APP_NAME}:latest

.PHONY: up
up: ## Start all docker containers
	@docker compose -f deployments/local/compose.yaml -p ${APP_NAME} up --build -d

.PHONY: down
down: ## Stop all docker containers
	@docker compose -f deployments/local/compose.yaml -p ${APP_NAME} down

.PHONY: rebuild
rebuild: ## Stop all docker containers, rebuild the pqbot image, and start all containers again
	make down
	make build
	make up

.PHONY: logs
logs: ## Show logs for pqbot:latest container
	@docker compose -f deployments/local/compose.yaml -p ${APP_NAME} logs ${APP_NAME} -f

.PHONY: sh
sh: ## Open shell for pqbot:latest container
	@docker compose -f deployments/local/compose.yaml -p ${APP_NAME} exec ${APP_NAME} sh

.PHONY: migrate
migrate: ## Run all migrations
	@docker compose -f deployments/local/compose.yaml -p ${APP_NAME} exec ${APP_NAME} alembic upgrade head

.PHONY: test
test: ## Run all tests
	@PYTHONDONTWRITEBYTECODE=1 pytest -vv

.PHONY: test-pdb
test-pdb: ## Run all tests with debugger
	@PYTHONDONTWRITEBYTECODE=1 pytest -vv --pdb
