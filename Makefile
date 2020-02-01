.PHONY: console
## Creates an ipython console with the app, db,  models, factories, and schema instances loaded in the session.
console:
	docker-compose exec api pipenv run flask shell

.PHONY: shell
## Creates a bash shell inside the `api` container
shell:
	docker-compose exec api bash

.PHONY: worker
## Creates a shell in the `worker` container
worker:
	docker-compose exec worker bash

.PHONY: test
## Runs the tests
test:
	docker-compose exec api bash -c "FLASK_ENV=testing ENV_FOR_DYNACONF=testing pipenv run pytest"

.PHONY: test-dev
## Runs the tests continuously on file changes
test-dev:
	docker-compose exec api bash -c "FLASK_ENV=testing ENV_FOR_DYNACONF=testing pipenv run ptw -- --testmon"

.PHONY: psql
## Creates a postgres shell in the `db` container
psql:
	docker-compose exec db psql -U postgres human_factor

.PHONY: redis-cli
## Creates a redis cli
redis-cli:
	docker run --link api_redis_1:redis --net api_default -it airdock/redis-client

.PHONY: migrate
## Flask db upgrade to the latest version of the schema
migrate:
	docker-compose exec api pipenv run flask db upgrade

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
