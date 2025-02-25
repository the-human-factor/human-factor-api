# Human Factor

[![CircleCI](https://circleci.com/gh/the-human-factor/human-factor-api/tree/master.svg?style=svg&circle-token=4b99181a5781d38ac02b3f0668f9156b532643e0)](https://circleci.com/gh/the-human-factor/human-factor-api/tree/master)

## Quickstart


### Requirements
You'll need to have Docker and docker-compose installed. If you're on a Mac, install [Docker for Mac](https://docs.docker.com/docker-for-mac/install/).


### Up and running
To bring up a running dev environment run the following commands

```bash
$ docker-compose up -d
$ make migrate
```

You should see output that looks like this:

```
$ docker-compose up -d
Creating network "human-factor-api_default" with the default driver
Creating volume "human-factor-api_devdb" with default driver
Creating human-factor-api_db_1 ... done
Creating human-factor-api_api_1 ... done

$ make migrate
docker-compose exec api pipenv run flask db upgrade
Loading .env environment variables…
[2019-07-02 19:38:39,064] INFO in app: App configured to talk to DB: postgres://postgres:@db/human_factor
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> fd19fa038408, Adds initial models
```

You can check that you have a working setup by doing

```
$ docker-compose ps
         Name                       Command               State            Ports
-----------------------------------------------------------------------------------------
human-factor-api_api_1   ./bin/wait-for-postgres.sh ...   Up      0.0.0.0:9000->9000/tcp
human-factor-api_db_1    docker-entrypoint.sh postg ...   Up      0.0.0.0:32785->5432/tcp
```

## Developing

Developing locally is done via docker-compose, therefore you can use the normal docker-compose commands to interact with the containers. Below are a few examples

### Logging

```
docker-compose logs -f <service-name>
```

Where service name can be either `api` or `db`

### Make targets - `make help`

For convenience we have several make targets as shorthands for docker-compose commands.


### Installing deps

We use [pipenv](https://github.com/pypa/pipenv) to manage our python dependencies and virtualenvs. To install new deps you can simply go into the `api` container (`make shell`) and do

```
# pipenv install <dependency>
```

### Recreate the db and blow away old versions

rm migrations/versions/*
make db-reset

make shell
pipenv shell

flask db migrate
flask db upgrade
