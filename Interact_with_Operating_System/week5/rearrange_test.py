#!/usr/bin/env python3

from rearrange import rearrange_name
import unittest

class TestRearrange(unittest.TestCase):
    def test_basic(self):
        testcase = 'love, ada'
        expected = 'ada love'
        self.assertEqual(rearrange_name(testcase),expected)
    def test_empty(self):
        testcase=''
        expected=''
        self.assertEqual(rearrange_name(testcase),expected)
    def test_double_name(self):
        testcase = 'hopper, grace M.'
        expected = 'grace M. hopper'
        self.assertEqual(rearrange_name(testcase),expected)
    def test_one_name(self):
        testcase = 'agron'
        expected = 'agron'
        self.assertEqual(rearrange_name(testcase),expected)


unittest.main()