# -*- coding: utf-8 -*-

fi = open('word_freqs.txt')

wc = {}
for line in fi:
    data = line.split()
    count = int(data[0])
    if data[3] in wc:
        wc[data[3]] += count
    else:
        wc[data[3]] = count

fi.close()
fi = open('gene.train')
fo = open('gene.rare.group.train','w')

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


for line in fi:
    if len(line) <= 1:
        fo.write(line)
    else:
        data = line.split()
        #print line
        word = data[0]
        #word = word.lower()
        if wc[word] < 5:
            if isNumeric(word):
                fo.write('_NUM_' + ' ' + data[1] + '\n')
            elif isAllCapital(word):
                fo.write('_ALLCAP_' + ' ' + data[1] + '\n')
            elif isLastCapital(word):
                fo.write('_LASTCAP_' + ' ' + data[1] + '\n')
            else:
                fo.write('_RARE_' + ' ' + data[1] + '\n')
        else:
            fo.write(data[0] + ' ' + data[1] + '\n')

fo.close()
fi.close()
