#! /usr/bin/python

__author__="Alexander Rush <srush@csail.mit.edu>"
__date__ ="$Sep 12, 2012"

import sys, json
from collections import defaultdict
import math

"""
Count rule frequencies in a binarized CFG.
"""

def sentence_iterator(copus_iterator):
    for l in copus_iterator:
        yield l.split()

class CKYParser:

    def __init__(self):
        self.unary = {}
        self.binary = {}
        self.nonterm = {}
        self.wordcounts = {}
        self.fi = open("parser_train.counts.out")
        self.load()

    def load(self):

        for line in self.fi:
            data = line.split()
            count = int(data[0])
            T = data[1]
            sym = data[2]
            if cmp(T, "NONTERMINAL") == 0:
                self.nonterm.setdefault(sym, 0)
                self.nonterm[sym] += count
            if cmp(T, "UNARYRULE") == 0:
                word = data[3]
                self.unary.setdefault((sym, word), 0)
                self.unary[(sym, word)] += count
            if cmp(T, "BINARYRULE") == 0:
                y1 = data[3]
                y2 = data[4]
                self.binary.setdefault((sym, y1, y2), 0)
                self.binary[(sym, y1, y2)] += count

        self.fi.close()
        self.fi = open("wordcounts.txt")

        for line in self.fi:
            data = line.split()
            word = data[0]
            count = int(data[1])
            self.wordcounts.setdefault(word, 0)
            self.wordcounts[word] += count
        self.fi.close()

    """important function"""
    def q1(self, sym, word):
        if (sym, word) in self.unary:
            return 1.0 * self.unary[(sym, word)] / self.nonterm[sym]
        elif word in self.wordcounts and self.wordcounts[word] < 5 and  (sym, "_RARE_") in self.unary:
            return 1.0 * self.unary[(sym, "_RARE_")] / self.nonterm[sym]
        elif not word in self.wordcounts and (sym, "_RARE_") in self.unary:
            return 1.0 * self.unary[(sym, "_RARE_")] / self.nonterm[sym]
        else:
            return 0.0

    def q2(self, sym, y1, y2):
        if (sym, y1, y2) in self.binary:
            return 1.0 * self.binary[(sym, y1, y2)] / self.nonterm[sym]
        else:
            return 0.0
    
    def getJson(self, st, ed, sentence, sym, bp):
        if st == ed:
            return '["' + sym + '", "' + sentence[st] + '"]'
        (y1, y2, mid)  =  bp[st][ed][sym]
        return '["' + sym + '", ' + self.getJson(st, mid, sentence, y1, bp) + ", " + self.getJson(mid+1, ed, sentence, y2, bp) + ']'


    def parse(self, sentence):
        s_len = len(sentence)
        pi = [[defaultdict(float) for x in range(s_len)] for y in range(s_len)]
        bp = [[defaultdict() for x in range(s_len)] for y in range(s_len)]
        for i in range(0, s_len):
            w = sentence[i]
            for sym in self.nonterm:
                pi[i][i][sym] = self.q1(sym, w)

        for l in range(1, s_len):
            for i in range(0, s_len-l):
                j = i + l
                for (sym, y1, y2), count in self.binary.iteritems():
                        for s in range(i, j):
                            if self.q2(sym, y1, y2) * pi[i][s][y1] * pi[s+1][j][y2] > pi[i][j][sym]:
                                pi[i][j][sym] = self.q2(sym, y1, y2) * pi[i][s][y1] * pi[s+1][j][y2] 
                                bp[i][j][sym] = (y1, y2, s)

        print pi[0][s_len-1]['SBARQ']
        return self.getJson(0, s_len-1, sentence, 'SBARQ', bp)
        

def replaceRare():
    rareword = []
    f = open("wordcounts.txt")
    for line in f:
        data = line.split()
        word = data[0]
        count = int(data[1])
        if count < 5:
            rareword.append(word)
    f.close()
    f = open("parse_train.dat")
    fo = open("parse_train_rare.dat", "w")
    for line in f:
        for rw in rareword:
            rw = '"' + rw + '"'
            line = line.replace(rw, '"_RARE_"')
        fo.write(line)

    fo.close()
    f.close()


if __name__ == "__main__": 
    replaceRare()

    parser = CKYParser()
    fo = open("parse_test.out", "w")
    f = open("parse_test.dat")
    for sentence in sentence_iterator(f):
        print sentence
        fo.write( parser.parse(sentence) + "\n")

