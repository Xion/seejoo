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
        @return: Whether the item could be added
        '''
        # Special case for insertion in the current node
        if not path:
            if self.data:   return False
            self.data = data
            return True
        
        node, tree_path = self._traverse(path)
        if path == tree_path:   return False
        
        new_node = PrefixTreeNode(data)
        
        # Relocate nodes that should be children of the newly created one
        rest = path[len(tree_path):]
        to_delete = []
        for label, child in node.children.items():
            if label.startswith(rest):
                new_label = label[len(rest):]
                new_node.children[new_label] = child
                to_delete.append(label)
        for label in to_delete:
            del node.children[label]
        
        node.children[rest] = new_node
        return True
    
    def search(self, prefix):
        '''
        Searches for all nodes that match given prefix.
        @return: A dictionary of matches, with values being data
        of nodes found
        '''
        res = {}
        node, path = self._traverse(prefix)
        
        # Do a DFS from given node
        stack = [(path, node)]
        while len(stack) > 0:
            curr_prefix, curr_node = stack.pop()
            rest = prefix[len(curr_prefix):]
            if rest:
                # Keep looking: try child nodes,
                # but only those that go along the path of the search prefix
                for child_label, child_node in curr_node.children.items():
                    if child_label.startswith(rest) or rest.startswith(child_label):
                        stack.append((curr_prefix + child_label, child_node))
            else:
                # This path is exhausted so we reached at some viable search result
                res[curr_prefix] = curr_node
                
        return res
            
    def __contains__(self, key):
        ''' 'in' operator. '''
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False
    
    def __getitem__(self, key):
        ''' Indexing operator. '''
        node, tree_path = self._traverse(key)
        if tree_path == key:    return node.data
        else:                   raise KeyError, key
        
    def __str__(self):
        return "%s --> (%s)" % (self.data, ",".join(self.children.keys()))
    

# Tree is just its root node
PrefixTree = PrefixTreeNode
