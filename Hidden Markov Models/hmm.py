#/usr/bin/python

import sys
from collections import defaultdict
import math

"""
Count n-gram frequencies in a data file and write counts to
stdout. 
"""

def simple_conll_corpus_iterator(corpus_file):
    """
    Get an iterator object over the corpus file. The elements of the
    iterator contain (word, ne_tag) tuples. Blank lines, indicating
    sentence boundaries return (None, None).
    """
    l = corpus_file.readline()
    while l:
        line = l.strip()
        if line: # Nonempty line
            # Extract information from line.
            # Each line has the format
            # word pos_tag phrase_tag ne_tag
            fields = line.split(" ")
            ne_tag = fields[-1]
            #phrase_tag = fields[-2] #Unused
            #pos_tag = fields[-3] #Unused
            word = " ".join(fields[:-1])
            yield word, ne_tag
        else: # Empty line
            yield (None, None)                        
        l = corpus_file.readline()

def sentence_iterator(corpus_iterator):
    """
    Return an iterator object that yields one sentence at a time.
    Sentences are represented as lists of (word, ne_tag) tuples.
    """
    current_sentence = [] #Buffer for the current sentence
    for l in corpus_iterator:        
            if l==(None, None):
                if current_sentence:  #Reached the end of a sentence
                    yield current_sentence
                    current_sentence = [] #Reset buffer
                else: # Got empty input stream
                    sys.stderr.write("WARNING: Got empty input file/stream.\n")
                    raise StopIteration
            else:
                current_sentence.append(l) #Add token to the buffer

    if current_sentence: # If the last line was blank, we're done
        yield current_sentence  #Otherwise when there is no more token
                                # in the stream return the last sentence.

def test_corpus_iterator(corpus_file):
    """
    Get an iterator object over the test corpus file. The elements of the
    iterator contain (word, ne_tag) tuples. Blank lines, indicating
    sentence boundaries return (None, None).
    """
    l = corpus_file.readline()
    while l:
        line = l.strip()
        if line: # Nonempty line
            # Extract information from line.
            # Each line has the format
            # word pos_tag phrase_tag ne_tag
            word = line
            #ne_tag = fields[-1]
            #phrase_tag = fields[-2] #Unused
            #pos_tag = fields[-3] #Unused
            #word = " ".join(fields[:-1])
            yield word
        else: # Empty line
            yield None                        
        l = corpus_file.readline()

def test_sentence_iterator(corpus_iterator):
    
    current_sentence = [] #Buffer for the current sentence
    for l in corpus_iterator:        
            if l==None:
                if current_sentence:  #Reached the end of a sentence
                    yield current_sentence
                    current_sentence = [] #Reset buffer
                else: # Got empty input stream
                    sys.stderr.write("WARNING: Got empty input file/stream.\n")
                    raise StopIteration
            else:
                current_sentence.append(l) #Add token to the buffer

    if current_sentence: # If the last line was blank, we're done
        yield current_sentence  #Otherwise when there is no more token
                                # in the stream return the last sentence.


def get_ngrams(sent_iterator, n):
    """
    Get a generator that returns n-grams over the entire corpus,
    respecting sentence boundaries and inserting boundary tokens.
    Sent_iterator is a generator object whose elements are lists
    of tokens.
    """
    for sent in sent_iterator:
         #Add boundary symbols to the sentence
         w_boundary = (n-1) * [(None, "*")]
         w_boundary.extend(sent)
         w_boundary.append((None, "STOP"))
         #Then extract n-grams
         ngrams = (tuple(w_boundary[i:i+n]) for i in xrange(len(w_boundary)-n+1))
         for n_gram in ngrams: #Return one n-gram at a time
            yield n_gram        

# Useful function to judge the type of rare words
def isNumeric(word):
    for c in word:
        if c.isdigit():
            return True
    return False

def isAllCapital(word):
    for c in word:
        if c.islower():
            return False
    return True

def isLastCapital(word):
    return word[len(word)-1].isupper()



class Hmm(object):
    """
    Stores counts for n-grams and emissions. 
    """

    def __init__(self, n=3):
        assert n>=2, "Expecting n>=2."
        self.n = n
        self.emission_counts = defaultdict(int)
        self.ngram_counts = [defaultdict(int) for i in xrange(self.n)]
        self.all_states = set()

    def train(self, corpus_file):
        """
        Count n-gram frequencies and emission probabilities from a corpus file.
      """
        ngram_iterator = \
            get_ngrams(sentence_iterator(simple_conll_corpus_iterator(corpus_file)), self.n)

        for ngram in ngram_iterator:
            #Sanity check: n-gram we get from the corpus stream needs to have the right length
            assert len(ngram) == self.n, "ngram in stream is %i, expected %i" % (len(ngram, self.n))
            
            tagsonly = tuple([ne_tag for word, ne_tag in ngram]) #retrieve only the tags   
            
            for i in xrange(2, self.n+1): #Count NE-tag 2-grams..n-grams
                self.ngram_counts[i-1][tagsonly[-i:]] += 1
            
            if ngram[-1][0] is not None: # If this is not the last word in a sentence
                self.ngram_counts[0][tagsonly[-1:]] += 1 # count 1-gram
                self.emission_counts[ngram[-1]] += 1 # and emission frequencies

            # Need to count a single n-1-gram of sentence start symbols per sentence
            if ngram[-2][0] is None: # this is the first n-gram in a sentence
                self.ngram_counts[self.n - 2][tuple((self.n - 1) * ["*"])] += 1
    
    def q(self, t_2, t_1, t):
        if self.ngram_counts[1][(t_2,t_1)] == 0:
            return 0
        return self.ngram_counts[2][(t_2, t_1, t)] * 1.0 / self.ngram_counts[1][(t_2, t_1)]
    
    #emission probability, e(word|tag)
    def e(self, word, tag):
        if self.emission_counts[(word, 'O')] + self.emission_counts[(word,'I-GENE')] < 5:
            """
            group the rare words to different types
            """
            if isNumeric(word):
                return self.emission_counts[('_NUM_', tag)] * 1.0 / self.ngram_counts[0][(tag,)]
            elif isAllCapital(word):
                return self.emission_counts[('_ALLCAP_', tag)] * 1.0 / self.ngram_counts[0][(tag,)]
            elif isLastCapital(word):
                return self.emission_counts[('_LASTCAP_', tag)] * 1.0 / self.ngram_counts[0][(tag,)]
            else:
                return self.emission_counts[('_RARE_', tag)] * 1.0 / self.ngram_counts[0][(tag,)]
        
        return self.emission_counts[(word, tag)] * 1.0/ self.ngram_counts[0][(tag,)]

    """
    the first part of the assignments can use this function to predict the tags
    """
    def predict_p1(self, sentence):
        s_len = len(sentence)
        K = ['O', 'I-GENE']
        Y = []
        for i in range(0, s_len):
            w = sentence[i]
            if self.e(w, 'O') >  self.e(w, 'I-GENE'):
                Y.append('O')
            else:
                Y.append('I-GENE')

        return Y

    def predict_p3(self, sentence):
        
        s_len = len(sentence)
        K = [['O', 'I-GENE'] for x in range(0, s_len)]
        K.append(['*'])
        K.append(['*'])
        pi = [defaultdict(float) for x in range(0, s_len+5)]
        bp = [defaultdict(str) for x in range(0, s_len+5)]
        pi[-1][('*', '*')] = 1
        for i in range(0, s_len):
            w = sentence[i]
            for t_1 in K[i-1]:
                for t in K[i]:
                    for t_2 in K[i-2]:
                        """
                        Multiply a big number 10000  to prevent too much small float multiplication always yields zero
                        Actually can use log to transform multiplication to addition
                        """
                        if pi[i][(t_1, t)] < pi[i-1][(t_2, t_1)] * self.q(t_2, t_1, t) * self.e(w, t) * 100000:
                           pi[i][(t_1, t)] = pi[i-1][(t_2, t_1)] * self.q(t_2, t_1, t) * self.e(w, t) * 100000
                           bp[i][(t_1, t)] = t_2
        _max = 0
        Y = ['O' for i in range(0, s_len)]
        for t_1 in K[s_len-2]:
            for t in K[s_len-1]:
                if pi[s_len-1][(t_1, t)] * self.q(t_1, t, 'STOP') * 100000 > _max:
                    _max = pi[s_len-1][(t_1, t)] * self.q(t_1, t, 'STOP') * 100000
                    Y[s_len-1] = t
                    Y[s_len-2] = t_1
        
        for i in range(s_len-3, -1, -1):
            Y[i] = bp[i+2][(Y[i+1], Y[i+2])]    
        
        return Y
                        

    def write_counts(self, output, printngrams=[1,2,3]):
        """
        Writes counts to the output file object.
        Format:

        """
        # First write counts for emissions
        for word, ne_tag in self.emission_counts:            
            output.write("%i WORDTAG %s %s\n" % (self.emission_counts[(word, ne_tag)], ne_tag, word))


        # Then write counts for all ngrams
        for n in printngrams:            
            for ngram in self.ngram_counts[n-1]:
                ngramstr = " ".join(ngram)
                output.write("%i %i-GRAM %s\n" %(self.ngram_counts[n-1][ngram], n, ngramstr))

    def read_counts(self, corpusfile):

        self.n = 3
        self.emission_counts = defaultdict(int)
        self.ngram_counts = [defaultdict(int) for i in xrange(self.n)]
        self.all_states = set()

        for line in corpusfile:
            parts = line.strip().split(" ")
            count = float(parts[0])
            if parts[1] == "WORDTAG":
                ne_tag = parts[2]
                word = parts[3]
                self.emission_counts[(word, ne_tag)] = count
                self.all_states.add(ne_tag)
            elif parts[1].endswith("GRAM"):
                n = int(parts[1].replace("-GRAM",""))
                ngram = tuple(parts[2:])
                self.ngram_counts[n-1][ngram] = count


if __name__ == "__main__":

    # Initialize a trigram counter
    hmm = Hmm(3)
    # training file after replacing some rare words 
    hmm.train(open('gene.rare.group.train'))
    
    test_file = test_corpus_iterator(open('gene.test'))
    #test_file = test_corpus_iterator(open('gene.dev'))
    test_sentences = test_sentence_iterator(test_file)
    fo = open('gene_test.p3.out', 'w')
    #fo = open('gene_dev.p3.out', 'w')

    for sentence in test_sentences:
        print sentence
        Y = hmm.predict_p3(sentence)
        for i in range(0, len(sentence)):
            fo.write(sentence[i] + " " + Y[i] + '\n')
        fo.write("\n")
    fo.close()
        
