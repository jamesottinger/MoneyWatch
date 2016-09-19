import unittest
from flask import current_app
#from app import create_app, db
from moneywatch import moneywatchengine

class MoneyWatchTestCase(unittest.TestCase):
    def setUp(self):
        #self.app = create_app('testing')
        #self.app_context = self.app.app_context()
        #self.app_context.push()
        #db.create_all()
        pass

    def tearDown(self):
        #db.session.remove()
        #db.drop_all()
        #self.app_context.pop()
        pass

    #def test_app_exists(self):
    #    self.assertFalse(current_app is None)

    #def test_app_is_testing(self):
    #    self.assertTrue(current_app.config["TESTING"])

    def test_moneywatch_dateqiftoint(self):
        """test h_dateqiftoint function
        """
        self.assertEqual(20080401,
            moneywatchengine.h_dateqiftoint("4/1'2008"))

        self.assertEqual(20091231,
            moneywatchengine.h_dateqiftoint("12/31'2009"))
