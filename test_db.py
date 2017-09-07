import Database as db
from unittest import main, TestCase
from collections import namedtuple
from itertools import starmap

logintuple = namedtuple('Login', ['user', 'pwd'])

class TestLogin(TestCase):
    @classmethod
    def setUpClass(cls):
        db.reset_database()
        cls.login = logintuple('fred', '1234')
        cls.user_id = db.Login.register(*cls.login)

    def test_login(self):
        user = db.Login(*self.login)
        self.assertEqual(self.user_id, user.user_id)

    def test_verify(self):
        user = db.Login(*self.login)
        self.assertTrue(user.verify_password(self.login.pwd))

    def test_update(self):
        user = db.Login(*self.login)
        self.__class__.login = logintuple('sarah', 'salt')
        user.username = self.login.user
        user.update_login(self.login.pwd)

        self.assertTrue(user.verify_password(self.login.pwd))
        relogin = db.Login(*self.login)
        self.assertEqual(self.user_id, relogin.user_id)

class Test_Users(TestCase):
    @classmethod
    def setUpClass(cls):
        db.reset_database()
        usernames = ['bob', 'person', 'rick', 'potato']
        passwords = ['1234', 'secure', 'potato', 'nomnom']
        cls.medicare = ['132323231', '1230939093', '90303990', '03908030']
        cls.login = list(starmap(logintuple, zip(usernames, passwords)))
        cls.user_id = [db.Users.register(*login) for login in cls.login]

    def test_all(self):
        expected = [db.Users(*login).user_id for login in self.login]
        self.assertListEqual(expected, [user['user_id'] for user in db.Users.get_all()])

    def test_update(self):
        for login, med_id in zip(self.login, self.medicare):
            user = db.Users(*login)
            user.medicare_id = med_id
            user.update_data()
            self.assertEqual(med_id, db.Users(*login).medicare_id)

    def test_history(self):
        pass

    def test_request(self):
        pass

    def test_valid_medicare(self):
        pass

    def test_medicare_gen(self):
        med_id = db.Users.generate_medicare()
        existing = [user['medicare_id'] for user in db.Users.get_all()]
        self.assertNotIn(med_id, existing)

if __name__ == '__main__':
    main()
