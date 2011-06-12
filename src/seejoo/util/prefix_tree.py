'''
Created on 2011-06-12

@author: xion

A generalized prefix tree class.
'''

class PrefixTreeNode(object):
    '''
    A generalized prefix tree node. Node contains:
    - data (any object)
    - links to children, each of them (i.e. links) labeled with a string
    '''
    def __init__(self, data = None):
        ''' Initializes the prefix tree node. '''
        self.data = data
        self.children = {}
    
    def _traverse(self, path):
        '''
        Internal function that traverses the prefix tree, searching for
        node which lies at the end of given path.
        Returns result of traversal which can be either a node
        found at the end of the path or a node where a divergence
        has been found and new node should potentially be inserted.
        @param path: A string determining the path in tree to traverse
        @return: 2-tuple: a node and a string path in tree that was traversed
        '''
        if not path:    return self, ""
        
        node = self
        ahead = path
        while len(ahead) > 0:
            # Pick a path to go down
            for c in sorted(node.children.keys(), key = len, reverse = True):
                if len(c) > len(ahead): continue
                if ahead.startswith(c):
                    node = node.children[c]
                    ahead = ahead[len(c):]
                    break
            else:
                # No path to go down;
                # either a divergence or leaf
                return node, path[:path.find(ahead)]
        
        return node, path   # Found a match
    
    def get(self, path):
        '''
        Retrieves an item from this node's subtree if it exists.
        @note: This node is part of its subtree so its key should prefix
        the parameter of this function for anything to be found
        @return: Data of the item or None if it could not be found
        '''
        node, tree_path = self._traverse(path)
        return node.data if tree_path == path else None
    
    def add(self, path, data):
        '''
        Adds an item to this node subtree.
        @note: Given path should be valid within subtree, i.e.
        path.startswith(self.key) must be True
        @return: Whether the item could be added
        '''
        if not path:
            # Special case for insertion in the node itself
            if self.data:   return False
            self.data = data
            return True
        
        node, tree_path = self._traverse(path)
        if not node:    raise ValueError, "Invalid prefix tree path"
        
        if path == tree_path:   return False
        
        remaining = path[len(tree_path):]
        node.children[remaining] = PrefixTreeNode(data)
        return True
            
        
    def __str__(self):
        return str(self.__dict__)
