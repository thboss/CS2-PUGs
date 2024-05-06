import json
import sys
import os
from yoyo import get_backend, read_migrations


if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/config.json") as file:
        config = json.load(file)


def migrate(direction):
    """ Apply Yoyo migrations for a given PostgreSQL database. """
    db_connect_url = 'postgresql://{user}:{password}@{host}:{port}/{database}'
    backend = get_backend(db_connect_url.format(**config['db']))
    migrations = read_migrations('./migrations')
    print('Applying migrations:\n' +
          '\n'.join(migration.id for migration in migrations))

    with backend.lock():
        if direction == 'up':
            backend.apply_migrations(backend.to_apply(migrations))
        elif direction == 'down':
            backend.rollback_migrations(backend.to_rollback(migrations))
        else:
            raise ValueError('Direction argument must be "up" or "down"')


if __name__ == '__main__':
    migrate(sys.argv[1])
