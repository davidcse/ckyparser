import copy
import math

class POSNotFoundException(Exception):
    pass

# a single cell in a 2D array table for the CKY parser
class ckyModelCell:
    # init prob dictionary to 0
    def __init__(self,  nonterminals, grammar):
        self.prob = {}
        self.triple = {}
        self.grammar = grammar
        self.nonterminals = nonterminals
        for i in nonterminals:
            self.prob[i] = 0

    def get(self, pos):
        if pos in self.prob:
            return self.prob.get(pos)
        else:
            print("Not found : " + pos)
            for key in self.prob:
                print("key: " + str(key) + " val: " + str(self.prob[key]))
            raise POSNotFoundException

    def set(self, pos, probability):
        if pos in self.prob:
            self.prob.update({pos : probability})
        else:
            raise POSNotFoundException

    def set_triple(self, pos, triple):
        self.triple[pos] = triple

    def update_if_greater(self,pos,probability):
        prob = self.get(pos)
        if(probability > prob):
            self.set(pos,probability)
            return True
        return False

    #checks if there is a rule that transitions to the word
    def rule_transition(self,word):
        for pos in self.prob:
            temp_rule = (pos, word)
            if temp_rule in self.nonterminals:
                self.prob[pos] = math.log(self.grammar[pos],2)


class ckyModelTable:
    def __init__(self,words,grammar, nonterminals):
        self.words = copy.deepcopy(words)
        self.grammar = copy.deepcopy(grammar)
        self.table = []
        self.nonterminals = nonterminals
        self.initTable(self.table, len(words)+1, self.nonterminals, self.grammar)


    # inits the 2-D table for cky parsing.
    def initTable(self, table, dimension_length, nonterminals, grammar):
        for i in range(dimension_length):
            row = []
            for j in range(dimension_length):
                cell = ckyModelCell(nonterminals,grammar)
                row.append(cell)
            table.append(row)

    def index(self,x,y):
        return self.table[x][y]



class Triple:
    def __init__(self, splitIndex, transition_pos_1, transition_pos_2):
        self.splitIndex = splitIndex
        self.transition_pos_1 = transition_pos_1
        self.transition_pos_2 = transition_pos_2



class ckyTree:

    def __init__(self,words,grammar):
        self.words = copy.deepcopy(words)
        self.grammar = copy.deepcopy(grammar)
        self.nonterminals = self.get_grammar_nonterminals(grammar)
        self.score = ckyModelTable(words,grammar, self.nonterminals)
        self.back = ckyModelTable(words,grammar, self.nonterminals)


    def build(self):
        self.fill_diagonal()
        self.parse()

    def fill_diagonal(self):
        for i in range(len(self.words)):
            begin = i
            end = i+1
            curr_word = self.words[i]
            ckyCell = self.score.index(begin,end)
            ckyCell.rule_transition(curr_word)
            self.addUnary(self.score,self.back,begin,end)



    def parse(self):
        for span in range(2, len(self.words) + 1, 1):
            for begin in range(0,len(self.words) + 1 - span, 1):
                end = begin + span
                for split in range(begin+1,end-1,1):
                    for rule in self.grammar:
                        # only evaluate for binary grammary rule transitions
                        if(len(rule)<3):
                            continue
                        pos_A = rule[0]
                        pos_B = rule[1]
                        pos_C = rule[2]
                        ckyCellLeftTree = self.score.index(begin,split)
                        ckyCellRightTree = self.score.index(split, end)
                        # probabilities are multiplied, same as sum of log_2(prob), to avoid underflow
                        prob = ckyCellLeftTree.get(pos_B)  + ckyCellRightTree.get(pos_C) + math.log(self.grammar[rule],2)
                        ckyCellCurrent = self.score.index(begin, end)
                        isGreater = ckyCellCurrent.update_if_greater(pos_A, prob)
                        if(isGreater):
                            self.back.get(begin,end).set(A, Triple(split,pos_B,pos_C))
                    self.addUnary(self.score,self.back,begin,end)
        return self.buildTree(self.score,self.back)

    def addUnary(self, score,back,begin,end):
        added_new_rule = True
        unary_rules = list(filter(lambda x: len(x) ==2 and x in self.nonterminals,self.grammar.keys()))
        while(added_new_rule):
            added_new_rule = False
            for unary_r in unary_rules:
                pos_A  = unary_r[0]
                pos_B = unary_r[1]
                prob = math.log(self.grammar[unary_r],2) + self.score.index(begin,end).get(pos_B)
                updated = self.score.index(begin, end).update_if_greater(pos_A, prob)
                if(updated):
                    self.back.index(begin, end).set_triple(Triple(-1,pos_B,None))
                    added_new_rule = True

    # extracts the non-terminal POS from grammar,
    # consisting of iterable containing tuples of (A,B,C)
    # where each tuple is rule A--> B,C
    def get_grammar_nonterminals(self,grammar):
        nonterminals = []
        for rule in grammar:
            if(len(rule)==3): # for binary rule A--> B,C
                self.add_rule_nonrepeat(rule,nonterminals)
        return nonterminals


    # inserts elements of iterable ruleTuple, non-repeat into an array nonterminals
    def add_rule_nonrepeat(self,ruleTuple, nonterminals):
        for i in ruleTuple:
            if i not in nonterminals:
                nonterminals.append(i)

    def buildTree(self,score, back):
        print("built tree")
