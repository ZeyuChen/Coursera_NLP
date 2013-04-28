import pickle, sys, os
from itertools import izip


class IBMModel:
    def __init__(self, modelNum = 1, ibm1_path = 'ibm.model'):
        '''For 'ibm2_path', if IBM Model2 is used, it will be initlized from IBM Model 1'''
        self.modelNum = modelNum
        if modelNum == 2:
            self.ibm1_path = ibm1_path

    def _train_init(self, en_file, es_file):
        #IBM II parameter
        if self.modelNum == 1:
            self.t = {}
        else:
            self.q = {}
            with open(self.ibm1_path, 'r') as ibm1_file:
                self.t = pickle.load(ibm1_file)
            print 'ibm1 model loaded'
            
        #word count in en_file
        en_file.seek(0); es_file.seek(0)
        self.word_count = {}
        for line in en_file:
            line = '_NULL_ ' + line
            tokens = line.rstrip().split()
            for word in tokens:
                self.word_count[word] = self.word_count.get(word, 0) + 1
        

    def _calc_delta_dividend(self, en_tokens, es_tokens, i, j):
        es, en = es_tokens[i], en_tokens[j]
        #IBM I / II
        if self.modelNum == 1:
            return self.t.get((es, en), 1.0/self.word_count[en])
        else:
            l, m = len(es_tokens), len(en_tokens)
            return self.q.get((j, i, l, m), 1.0/(l+1))*self.t.get((es, en), 1.0/self.word_count[en])

    def _calc_delta_divisor(self, en_tokens, es_tokens, i):
        base = 0.0
        for j in range(0, len(en_tokens)):
            es, en = es_tokens[i], en_tokens[j]
            #IBM I / II
            if self.modelNum == 1:
                base += self.t.get((es, en), 1.0/self.word_count[en])
            else:
                l, m = len(es_tokens), len(en_tokens)
                base += self.t.get((es, en), 1.0/self.word_count[en]) * self.q.get((j, i, l, m), 1.0/(l+1))
        return base
        

    # i for es, j for en
    def _em_single_line(self, en_line, es_line, c, c2, c3, c4):
        en_line = '_NULL_ ' + en_line
        en_tokens = en_line.rstrip().split()
        es_tokens = es_line.rstrip().split()
        l, m = len(es_tokens), len(en_tokens)
        for i in range(len(es_tokens)):
            delta_divisor = self._calc_delta_divisor(en_tokens, es_tokens, i)
            for j in range(len(en_tokens)):
                en, es = en_tokens[j], es_tokens[i]
                delta_dividend = self._calc_delta_dividend(en_tokens, es_tokens, i, j)
                delta = float(delta_dividend)/delta_divisor
                c[(en, es)] = c.get((en, es), 0.0) + delta
                c2[en] = c2.get(en, 0) + delta
                #IBM I / II
                if self.modelNum == 2:
                    c3[(j, i, l, m)] = c3.get((j, i, l, m), 0.0) + delta
                    c4[(i, l, m)] = c4.get((i, l, m), 0.0) + delta
                
                

    def _em_iterations(self, en_file, es_file, iter_count):
        for cur_iter in range(0, iter_count):
            #print
            print '\niter: ' + str(cur_iter+1)
            #init  c:(en ,es)
            c, c2, c3, c4 = {}, {}, {}, {}
            en_file.seek(0); es_file.seek(0)
            #iter lines
            for en_line, es_line in izip(en_file, es_file):
                self._em_single_line(en_line, es_line, c, c2, c3, c4)
                sys.stdout.write('.')
            #update t parameter
            for (en, es), en_es_score in c.iteritems():
                self.t[(es, en)] = float(en_es_score)/c2[en]
            #IBM I / II   update q parameter
            if self.modelNum == 2:
                for (j, i, l, m), score in c3.iteritems():
                    self.q[(j, i, l, m)] = float(score)/c4[(i, l, m)]
                    
                

    def train(self, en_file = file('corpus.en'), es_file = file('corpus.es'), iter_count = 10):
        self._train_init(en_file, es_file)
        self._em_iterations(en_file, es_file, iter_count)


    def _parse_sent(self, en_tokens, es_tokens):
        ans = []
        for i in range(0, len(es_tokens)):
            max_j = 0; max_score = 0
            for j in range(0, len(en_tokens)):
                en, es = en_tokens[j], es_tokens[i]
                score = self.t.get((es, en), 0)
                #IBM I / II
                if self.modelNum == 2:
                    l, m = len(es_tokens), len(en_tokens)
                    score = score * self.q.get((j, i, l, m), 0)
                
                if score > max_score:
                    max_j, max_score = j, score
            ans.append(max_j)
        return ans

    def _print_parse_result(self, result, out_file, line_num):
        count = 1
        for i in result:
            out_file.write('%d %d %d\r\n'%(line_num, i, count))
            count += 1
            
    def parse_sents(self, en_file = file('dev.en'), es_file = file('dev.es'), out_path = 'dev.out'):
        en_file.seek(0); es_file.seek(0)
        with open(out_path, 'w') as out_file:
            line_num = 1
            for en_line, es_line in izip(en_file, es_file):
                en_line = '_NULL_ ' + en_line
                en_tokens = en_line.rstrip().split()
                es_tokens = es_line.rstrip().split()
                result = self._parse_sent(en_tokens, es_tokens)
                self._print_parse_result(result, out_file, line_num)
                line_num += 1
                sys.stdout.write('.')
                

    def save_parameter(self, save_path = 'ibm.model'):
        with open(save_path, 'wb') as save_file:
            #IBM I / II
            if self.modelNum == 1:
                pickle.dump(self.t, save_file)
            else:
                to_save = {'t':self.t, 'q':self.q}
                pickle.dump(to_save, save_file)
        

    def load_parameter(self, load_path = 'ibm.model'):
        with open(load_path, 'r') as load_file:
            #IBM I / II
            if self.modelNum == 1:
                self.t = pickle.load(load_file)
            else:
                loaded = pickle.load(load_file)
                self.t = loaded['t']
                self.q = loaded['q']

        
        
if __name__ == '__main__':
    try:
        #IBM Model I
        
        if_trained = False
        ibm = IBMModel()
        if not if_trained:
            print 'Training IBM Model I'
            ibm.train(iter_count = 5)
            print 'training done'
            ibm.save_parameter('ibm.model')
            print 'saving done'
        else:
            ibm.load_parameter('ibm.model')
            print 'loading done'

        ibm.parse_sents(file('test.en'), file('test.es'), 'alignment_test.p1.out')
        print 'parsing done'

        
        #IBM Model II
        
        if_trained = False
        ibm = IBMModel(2, 'ibm.model')
        if not if_trained:
            print 'Training IBM Model II'
            ibm.train(iter_count = 5)
            print 'training done'
            ibm.save_parameter('ibm2.model')
            print 'saving done'
        else:
            ibm.load_parameter('ibm2.model')
            print 'loading done'
        
        ibm.parse_sents(file('test.en'), file('test.es'), 'alignment_test.p2.out')
        print 'parsing done'
        
    except Exception, e:
        print e
    finally:
        os.system('pause')
