from functools import reduce
import ckyModel as ckyModel

grammar = {}


def grammar_insert_unarydata(grammar, unary_rule_arr):
    for rule in unary_rule_arr:
        if(rule.strip()==""):
            continue
        rule_components = rule.split("\t")
        rule_components.remove("")
        assert(len(rule_components) == 3)
        start_A, end_B, prob = rule_components[0],rule_components[1], rule_components[2]
        grammar[(start_A,end_B)] = float(prob)

def grammar_insert_binarydata(grammar, binary_rule_arr):
    for rule in binary_rule_arr:
        if(rule.strip()==""):
            continue
        rule_components = rule.split("\t")
        rule_components.remove("")
        assert(len(rule_components) == 4)
        start_A, end_B, end_C, prob = rule_components[0],rule_components[1], rule_components[2], rule_components[3]
        grammar[(start_A,end_B,end_C)] = float(prob)


unary_rule_data = open("ckyparse_input_unary.txt","r").read().split("\n")
binary_rule_data = open("ckyparse_input_binary.txt","r").read().split("\n")

grammar_insert_unarydata(grammar, unary_rule_data)
totalProb = reduce(lambda x,y:float(x)+float(y),grammar.values())
grammar_insert_binarydata(grammar, binary_rule_data)
totalProb = reduce(lambda x,y:float(x)+float(y),grammar.values())
words = "I am a tree".split()
if "" in words:
    words.remove("")
tree = ckyModel.ckyTree(words,grammar)
tree.build()
