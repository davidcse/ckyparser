from sys import argv
from functools import reduce
import tree
import copy

try:
    script, pcfgTreeFile = argv
except:
    print("usage: python pcfgInductor.py <train.tree>")
    exit(0)


class ChomskyNormalFormException(Exception):
    pass


# stores tuples of (POS, word) as key, number of times seen in training as value
# Stores counts of production rule POS[position 1] ===> word[position 2].
unary_rules = {}
# stores tuples of (POS, POS, POS) as key, num times seen in training as value.
# Stores counts of production rule POS[position 1] ===> POS[position 2]POS[position 3]
binary_rules = {}

# maps the non-terminal POS, to its transitioned POS in a nested dict. {POS : {(POS,POS):count}}
mapped_binary_rules = {}
# maps the non-terminal POS, to its transitioned Word in a nested dict. {POS : {WORD:count}}
mapped_unary_rules = {}



#####################################
#   DICTIONARY HELPERS
#####################################

# for count dictionary, increment the count seen. Init to 1, if seen key for first time.
def dict_safe_increment(dictionary, key):
    if(key not in dictionary):
        dictionary[key] = 1
    else:
        dictionary[key]+=1

# for nested count dictionary, increment the count seen.
# Init to 1, if seen nested key for first time.
# {key: {nestedkey: 1 }}
def nested_dict_safe_increment(dictionary, key, nestedkey):
    if(key not in dictionary):
        dictionary[key] = {nestedkey : 1 }
    elif(nestedkey not in dictionary[key]):
        dictionary[key][nestedkey] = 1
    else:
        dictionary[key][nestedkey] += 1

########################################
#   DICT INSERT HELPERS
########################################

# inserts ruleTuple (pos_label, word) into map for quick lookup on pos_label
def mapped_unary_rules_insert(ruleTuple):
    ruleCopy = copy.deepcopy(ruleTuple)
    pos_label = ruleCopy[0]
    # unary rule, list component only has one word
    word = ruleCopy[1][0]
    nested_dict_safe_increment(mapped_unary_rules, pos_label, word)


# inserts ruleTuple (pos_label, [pos_transition1,pos_transition2])
# into map for quick lookup on pos_label
def mapped_binary_rules_insert(ruleTuple):
    ruleCopy = copy.deepcopy(ruleTuple)
    pos_label = ruleCopy[0]
    transition_pos_list = ruleCopy[1]
    transition_pos_list.sort()
    transition_tuple = tuple(transition_pos_list)
    nested_dict_safe_increment(mapped_binary_rules, pos_label, transition_tuple)


# leaves original ruletuple unchanged, by copying it and creating a
# tuple where the first item is the start, and second item of tuple is word.
# inserts the new tuple rule into the unary_rules dict.
def unary_rules_insert(ruleTuple):
    ruleCopy = copy.deepcopy(ruleTuple)
    start_pos_label = ruleCopy[0]
    terminal_leaf_word = ruleCopy[1][0]
    r = (start_pos_label, terminal_leaf_word )
    # insert tuple into unary dict.
    dict_safe_increment(unary_rules , r )

# leaves original ruletupel unchanged, by copying it and creating a
# tuple where the first item is the start, and rest of tuple is transitioned pos_tag.
# inserts the new tuple rule into the binary_rules dict.
def binary_rules_insert(ruleTuple):
    ruleCopy = copy.deepcopy(ruleTuple)
    # insert  the left-hand side label(rule[0]) into front of production rule list.
    start_pos_label = ruleCopy[0]
    ruleCopy[1].sort() # consistent order for all list combinations with same contents
    ruleCopy[1].insert(0,start_pos_label)
    # convert the list into a tuple, preserving order.
    r = tuple(ruleCopy[1])
    # insert tuple into unary dict.
    dict_safe_increment(binary_rules , r )



# parses a node and its children for both binary and unary production rules
def parse_rules(node):
    rule = (node.label, [])
    # add the childnode labels as one of the outputs of the production rule
    for childnode in node.children:
        rule[1].append(childnode.label)
    # num output violates chomsky normal form
    if(len(rule[1])>2):
        raise ChomskyNormalFormException
    # is a terminal node
    elif(len(rule[1])==0):
        pass
    # is a unary rule
    elif(len(rule[1])== 1):
        unary_rules_insert(rule)
        mapped_unary_rules_insert(rule)
    # is a binary rule
    else:
        binary_rules_insert(rule)
        mapped_binary_rules_insert(rule)

######################################
#   HANDLE FILES
######################################
def deserializeTreeFile(pcfgTreeFile):
    # open serialized trees file for reading.
    pcfgTreeContent = open(pcfgTreeFile,'r')
    # one treeline contains a completely serialized tree
    treeline = pcfgTreeContent.readline()
    while(treeline):
        # use the trees library to parse and embed POS into a tree datastructure
        tree_instance = tree.Tree.from_str(treeline)
        # create a python generator, using the tree's bottom up function.
        postorder_traversal = tree_instance.bottomup()
        # Iterate generator for all nodes in tree.
        for node in postorder_traversal:
            parse_rules(node)
        treeline = pcfgTreeContent.readline()



#################################
#   PROBABILITIES
#################################

# laplace smooth formula
def laplace_smooth(count, totalcount, vocabsize):
    return (count + 1)/(totalcount + vocabsize + 1)


# calculates mle for a binary tuple rule from binary_rules dict.
def mle(tup,binary_rules):
    start_symbol = tup[0]
    # count transition start_symbol ===> (POS_1, POS_2), start_symbol = pos_1
    count_rule = binary_rules[tup]
    # start_symbol guaranteed to be seen in training for MLE probability.
    transition_dict = mapped_binary_rules.get(start_symbol)
    # count transitions of start_symbol ===> * (any tag rule)
    count_all_transitions = reduce(lambda x,y: x+y, transition_dict.values())
    rule_transition = tup[1:] # get the rest of tuple for the transition tags.
    count_rule_duplicate = transition_dict[rule_transition]
    assert(count_rule == count_rule_duplicate)
    mle_prob = count_rule / count_all_transitions
    return mle_prob


# returns unary rules, with each rule components stored in a list.
# returns a larger list of each unary rule list.
def laplace_smooth_unary_rules(unary_rules):
    filelines = [] # lines ready to write to file
    vocabsize = len(unary_rules)
    totalcount = reduce(lambda x,y: x + y, unary_rules.values())
    sum_prob =0
    for tup in unary_rules:
        count = unary_rules[tup]
        unary_rule_line = list(tup)
        laplace_prob = laplace_smooth(count,totalcount,vocabsize)
        sum_prob += laplace_prob
        unary_rule_line.append(str(laplace_prob))
        filelines.append(unary_rule_line)
    assert(len(filelines) == len(unary_rules))
    assert ( (1 - sum_prob) < 0.001)
    return filelines

# returns binary rules, with each rule components stored in a list.
# returns a larger list of each binary rule list.
def mle_binary_rules(binary_rules):
    filelines = [] # lines ready to write to file
    for tup in binary_rules:
        line = list(tup)
        mle_prob = mle(tup,binary_rules)
        line.append(str(mle_prob))
        filelines.append(line)
    assert(len(filelines) == len(binary_rules))
    return filelines


# takes a list, and turns into tab-separated string.
def form_tab_separated_str(list):
    outline = ""
    for column in list:
        outline += column
        outline += "\t"
    outline.strip("\t") # strip the last tab at end of line
    return outline

#########################
#   script
#########################

# fills dictionaries with file contents
deserializeTreeFile(pcfgTreeFile)
filelines_unary_rules = laplace_smooth_unary_rules(unary_rules)
filelines_binary_rules = mle_binary_rules(binary_rules)

# output file
u_file ="ckyparse_input_unary.txt"
b_file = "ckyparse_input_binary.txt"
out_unary = open(u_file,'w')
out_binary = open(b_file,'w')

# store into unary file
for u_line in filelines_unary_rules:
    assert(len(u_line)==3)
    outline = form_tab_separated_str(u_line)
    out_unary.write(outline + "\n")
print("written into : " + u_file)

# store into binary file
for bin_line in filelines_binary_rules:
    assert(len(bin_line)==4)
    outline = form_tab_separated_str(bin_line)
    out_binary.write(outline + "\n")
print("written into : " + b_file)
