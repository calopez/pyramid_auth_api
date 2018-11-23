import os
import sys
import transaction

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from .createuser import create

from ..system.user.models import Group
from ..system.model.meta import Base
from ..system.model.meta import (
    get_engine,
    get_session_factory,
    get_tm_session,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)

    engine = get_engine(settings)
    # Always enable UUID extension for PSQL
    # TODO: Convenience for now, because we assume UUIDs, but make this somehow configurable
    engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    from ..system.model import config_declarative_models
    config_declarative_models()

    Base.metadata.create_all(engine)

    session_factory = get_session_factory(engine)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)
        group = Group(name=Group.DEFAULT_ADMIN_GROUP_NAME, description="Super administrator")
        dbsession.add(group)
        create(dbsession, username="Carlos", email="carloslopez@me.com", password="some?pass", admin=True )


if __name__ == "__main__":
    main()
