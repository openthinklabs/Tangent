__author__ = 'KMDC'

class WildcardAlignment:
    def __init__(self, q_variable, q_location, c_tree, c_location):
        self.q_variable = q_variable
        self.q_location = q_location

        self.c_tree = c_tree
        self.c_location = c_location

        self.c_size = self.__subtree_size(c_tree)

        self.score = 0.0

    def __subtree_size(self, tree_root):
        current_size = 1

        if not tree_root.next is None:
            current_size += self.__subtree_size(tree_root.next)
        if not tree_root.above is None:
            current_size += self.__subtree_size(tree_root.above)
        if not tree_root.below is None:
            current_size += self.__subtree_size(tree_root.below)
        if not tree_root.over is None:
            current_size += self.__subtree_size(tree_root.over)
        if not tree_root.under is None:
            current_size += self.__subtree_size(tree_root.under)
        if not tree_root.pre_above is None:
            current_size += self.__subtree_size(tree_root.pre_above)
        if not tree_root.pre_below is None:
            current_size += self.__subtree_size(tree_root.pre_below)
        if not tree_root.within is None:
            current_size += self.__subtree_size(tree_root.within)
        if not tree_root.element is None:
            current_size += self.__subtree_size(tree_root.element)

        return current_size


    def __eq__(self, other):
        if isinstance(other, WildcardAlignment):
            return (self.q_location == other.q_location and
                    self.c_location == other.c_location)
        else:
            return False


    def same_substitution(self, other):
        if isinstance(other, WildcardAlignment):
            local_slt = self.c_tree.tostring()
            other_slt = other.c_tree.tostring()

            return local_slt == other_slt
        else:
            return None

    def __repr__(self):
        return ("<(" + str(self.q_variable.tag) + ", " + self.q_location + ")-(" +
                self.c_tree.tostring() + ", " + self.c_location + ")>")
