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

class TestUser(TestCase):
    @classmethod
    def setUpClass(cls):
        db.reset_database()
        usernames = ['bob', 'person', 'rick', 'potato']
        passwords = ['1234', 'secure', 'potato', 'nomnom']
        cls.medicare = ['132323231', '1230939093', '90303990', '03908030']
        cls.login = list(starmap(logintuple, zip(usernames, passwords)))
        cls.user_id = [db.User.register(*login) for login in cls.login]

    def test_all(self):
        unexpected = db.Login.register('random', 'password')
        expected = [db.User(*login).user_id for login in self.login]
        self.assertListEqual(expected, [user.user_id for user in db.User.get_all()])

    def test_update(self):
        for login, med_id in zip(self.login, self.medicare):
            user = db.User(*login)
            user.medicare_id = med_id
            user.update_data()
            self.assertEqual(med_id, db.User(*login).medicare_id)

    def test_history(self):
        pass

    def test_request(self):
        user = db.User(*self.login[0])
        request = {'amount':500, 'reason':'precription', 'request_date':'2017-03-02'}
        req_id = user.make_request(**request)
        request['request_id'] = req_id
        request['user_id'] = self.user_id[0]
        for key in ('processed_by', 'date_processed', 'approved'):
            request[key] = None
        self.assertEqual(request, user.get_requests()[0].__dict__)

        another = {'amount':200, 'reason':'test'}
        req_id = user.make_request(**another)
        request = filter(lambda r: r.request_id == req_id, user.get_requests())
        self.assertIsNotNone(next(request).request_date)

    def test_valid_medicare(self):
        pass

    def test_medicare_gen(self):
        med_id = db.User.generate_medicare()
        existing = [user.medicare_id for user in db.User.get_all()]
        self.assertNotIn(med_id, existing)
        self.assertNotEqual(med_id, db.User.generate_medicare())

class TestRebateRequest:
    def test_update(self):
        db.reset_database()
        username, pwd = 'johnti', 'defcon'
        db.User.register(username, pwd)
        user = db.User(username, pwd)
        user.make_request(amount=400, reason='why not')
        req = user.get_requests()
        req.approved = True
        req.update()
        self.assertEqual(req.__dict__, user.get_requests().__dict__)

class TestProfessional(TestCase):
    @classmethod
    def setUpClass(cls):
        db.reset_database()
        users = ['brinkley', 'freeze', 'doom']
        passwords = [' ', 'correct', 'asdf']
        cls.login = list(starmap(logintuple, zip(users, passwords)))
        cls.user_id = [db.MedicalProfessional.register(*login) for login in cls.login]

    def test_all(self):
        unexpected = db.User.register('random', 'password')
        expected = [db.MedicalProfessional(*login).user_id for login in self.login]
        self.assertListEqual(expected, [user.user_id for user in db.MedicalProfessional.get_all()])

if __name__ == '__main__':
    main()
