'''
Created on 2011-06-12

@author: xion

Contains unit tests for utility module.
'''
import unittest
from seejoo.util.prefix_tree import PrefixTreeNode


class PrefixTreeTest(unittest.TestCase):
    TEST_ITEMS = { 'abc': 1, 'abcd': 2, 'a': 3, 'ab': 4, '': 5 }

    def test_prefixtree(self):
        tree = PrefixTreeNode()

        for key, data in self.TEST_ITEMS.items():
            tree.add(key, data)

        for key, data in self.TEST_ITEMS.items():
            self.assertEquals(tree.get(key), data)

        print tree.search('a')
