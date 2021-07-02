import unittest
from emails import find_email

class EmailTest(unittest.TestCase):
    def test_basic(self):
        testcase = [None,'Blossom','Gill']
        expected = 'blossom@abc.edu'
        self.assertEqual(find_email(testcase),expected)
    def test_one_name(self):
        testcase = [None,'John']
        expected = 'Missing parameters'
        self.assertEqual(find_email(testcase),expected)
    def test_two_name(self):
        testcase = [None,'Roy','tsai']
        expected = 'No email address found'
        self.assertEqual(find_email(testcase),expected)

if __name__=='__main__':
    unittest.main()