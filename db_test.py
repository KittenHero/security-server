import Database
from unittest import main, TestCase

class TestLogin(TestCase):
    @classmethod
    def setUpClass(cls):
        Database.reset_database()
        cls.username = 'fred'
        cls.password = '1234'
        cls.user_id = Database.Login.register(cls.username, cls.password)

    def test_login(self):
        user = Database.Login(self.username, self.password)
        self.assertEqual(self.user_id, user.user_id)

    def test_verify(self):
        user = Database.Login(self.username, self.password)
        self.assertTrue(user.verify_password(self.password))

    def test_update(self):
        user = Database.Login(self.username, self.password)
        self.__class__.username = 'sarah'
        self.__class__.password = 'salt'
        user.username = self.username
        user.update_login(self.password)

        self.assertTrue(user.verify_password(self.password))
        relogin = Database.Login(self.username, self.password)
        self.assertEqual(self.user_id, relogin.user_id)

if __name__ == '__main__':
    main()
