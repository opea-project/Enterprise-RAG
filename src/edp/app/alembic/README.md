# Automatic EDP database migrations using Alembic

## Production

Database schema migrations are handled automatically with no administrative intervention required. Alembic migrations execute in the order determined by the `revision` files in the `alembic/versions` folder. These migrations run as part of the `entrypoint.sh` script within EDP containers, ensuring init containers verify database connectivity before proceeding. Since database configuration inherits from project settings, migrations work seamlessly out of the box. The `alembic upgrade head` command is idempotent, preventing issues during container restarts.

On the first run or if alembic finds any migrations, the edp-backend log will output alembic logs:
```bash
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> a4e67434b1cb, Initial migration
INFO  [alembic.runtime.migration] Running upgrade  -> bc829d1ad423, Add additional fields
```

## Development - adding new migrations

Create a dummy `.env` file:
```bash
DATABASE_USER=edp
DATABASE_PASSWORD=
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=enhanced_dataprep
```

To generate a migration you have to run a database:

```bash
docker run --rm --name postgres --env-file .env -p 5432:5432 postgres:16
```

To generate the initial migration run (this will probably be done already):

```bash
cd /src/edp/app
source .env
alembic revision --autogenerate -m "Initial migration"
```

Upgrade the database to current migration
```bash
cd /src/edp/app
source .env
alembic upgrade head
```

This is the place where you modify `models.py` file and add/remove columns. After modifcation you have to generate migrations as follows.

To generate additional migrations run:
```bash
# Implement changes in models, remember to import new models into alembic/env.py !
alembic revision --autogenerate -m "Some comment regarding changes etc.."
```

To test the initialization script, select a migration form history and then run it - this will run a specific migration on the db.
```bash
cd /src/edp/app
alembic history
alembic upgrade <revision_id>
# or run the full upgrade by using head as revision_id
```

Then build and run the docker image for edp:
```bash
cd src
docker build -f edp/Dockerfile -t edp-backend --build-arg HTTP_PROXY=$HTTP_PROXY --build-arg http_proxy=$http_proxy --build-arg HTTPS_PROXY=$HTTPS_PROXY  --build-arg https_proxy=$https_proxy --build-arg NO_PROXY=$NO_PROXY --build-arg no_proxy=$no_proxy .
docker run --rm --link postgres --env-file .env edp-backend # link is deprecated, alternatively use docker networks
```

This will run migrations:
```bash
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> a4e67434b1cb, Initial migration
INFO  [alembic.runtime.migration] Running upgrade  -> bc829d1ad423, Add additional fields
```
