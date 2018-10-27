from pyramid.settings import asbool


def includeme(config):
    config.add_directive('db_sanity_check', db_sanity_check)


def db_sanity_check(config):
    def callback():
        check = asbool(config.registry.settings.get("tm.sanity_check", True))
        if check:
            sanity_check_callback(config)
            config.commit()

    discriminator = ('db_sanity_check',)
    config.action(discriminator, callable=callback)


def sanity_check_callback(config):
    """Perform post-initialization sanity checks.

    This is run on every startup to check that the database table schema matches our model definitions. If there
    are un-run migrations this will bail out and do not let the problem to escalate later.

    See also: :ref:`websauna.sanity_check`.

    """
    import transaction
    from tm.system.model import get_engine
    from tm.system.model import get_session_factory
    from tm.system.model import get_tm_session
    from tm.system.model import sanitycheck
    from tm.system.model.meta import Base
    import sqlalchemy.exc

    engine = get_engine(config.registry.settings)
    session_factory = get_session_factory(engine)
    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)

        db_connection_string = config.registry.settings.get("sqlalchemy.url")

        try:
            if not sanitycheck.is_sane_database(Base, dbsession):
                raise SanityCheckFailed("The database sanity check failed. Check log for details.")
        except sqlalchemy.exc.OperationalError as e:
            msg = "The database {} is not responding.\nMake sure the database is running on your local computer or "
            "correctly configured in settings INI file."
            raise SanityCheckFailed(msg.format(db_connection_string)) from e
        dbsession.close()

class SanityCheckFailed(Exception):
    """Looks like the application has configuration which would fail to run."""

