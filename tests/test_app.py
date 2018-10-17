import unittest
import transaction

from pyramid import testing


def dummy_request(dbsession):
    return testing.DummyRequest(dbsession=dbsession)


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings={
            'sqlalchemy.url': 'sqlite:///:memory:'
        })
        self.config.include('tm.models')
        settings = self.config.get_settings()

        from tm.models import (
            get_engine,
            get_session_factory,
            get_tm_session,
            )

        self.engine = get_engine(settings)
        session_factory = get_session_factory(self.engine)

        self.session = get_tm_session(session_factory, transaction.manager)

    def init_database(self):
        from tm.models.meta import Base
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        from tm.models.meta import Base

        testing.tearDown()
        transaction.abort()
        Base.metadata.drop_all(self.engine)


class TestMyViewSuccessCondition(BaseTest):

    def setUp(self):
        super(TestMyViewSuccessCondition, self).setUp()
        self.init_database()

        from tm.models import MyModel

        model = MyModel(name='one', value=55)
        self.session.add(model)

    def test_passing_view(self):
        from tm.views.default import my_view
        info = my_view(dummy_request(self.session))
        self.assertEqual(info['one'].name, 'one')
        self.assertEqual(info['project'], 'Pyramid Scaffold')


class TestMyViewFailureCondition(BaseTest):

    def test_failing_view(self):
        from tm.views.default import my_view
        info = my_view(dummy_request(self.session))
        self.assertEqual(info.status_int, 500)
