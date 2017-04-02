from __future__ import division
import string
import math
import codecs
import json
import dill
import pickle
import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.externals import joblib
from nltk.corpus import stopwords

def clean_no_stemma_stopwords(text, as_list=True):
    tokens = [re.sub('[^.?!a-z]', '', w) for w in text.lower().strip().split() if w.isalpha() or re.search('[.!?](?:[ ]|$)', w)]
    if as_list:
        return tokens
    else:
        return ' '.join(tokens) 

def f(doc):
    return doc.lower().split(" ")

if __name__ == '__main__':
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K' 

    textbook = 'OS'

    TRAIN = True



    print('Loading corpus data')
    stopwords = set(stopwords.words('english'))

    try:
        domain = pickle.load(open('resources/domain.pkl',  'rb'))
    except:
        domain = pickle.load(open('resources/domain_2.pkl',  'rb'))

    keywords = set()
    for k in domain:
        keywords = keywords.union(set(list(map(str.lower, map(str, list(domain[k]))))))
    stopwords = stopwords - keywords

    if textbook == 'ADA':
        questions = [clean_no_stemma_stopwords(q, as_list=False) for q in json.load(open('resources/os_questions.json'))]
    else:
        questions = []

    contents = []
    os.chdir('resources/%s' %textbook)
    for filename in sorted(os.listdir('.')):
        if '__' in filename or '.DS_Store' in filename:
            continue
        try:
            f = open(filename, encoding='latin-1')
        except:
            f = open(filename)
        contents.append(clean_no_stemma_stopwords(f.read(), as_list=False))
        f.close()   

    os.chdir('../..')

    print('Training tfidf')
    sklearn_tfidf = TfidfVectorizer(norm='l2', 
                                    min_df=0,
                                    decode_error="ignore",
                                    strip_accents='unicode',  
                                    use_idf=True, 
                                    smooth_idf=False, 
                                    sublinear_tf=True, 
                                    tokenizer=f)
    tfidf_matrix = sklearn_tfidf.fit_transform(questions + contents)

    pickle.dump(sklearn_tfidf, open('models/tfidf_filterer_%s.pkl' %textbook.lower(), 'wb'))

    feature_names = sklearn_tfidf.get_feature_names()

    new_questions = []

    print()

    for i in range(0, len(questions)):
        feature_index = tfidf_matrix[i,:].nonzero()[1]
        tfidf_scores = zip(feature_index, [tfidf_matrix[i, x] for x in feature_index])
        word_dict = {w : s for w, s in [(feature_names[j], s) for (j, s) in tfidf_scores]}

        new_question = ''
        question = re.split('([.!?])', questions[i])
        question2 = []
        for k in range(len(question) - 1):
            if re.search('[!.?]', question[k + 1]):
                question2.append(question[k] + question[k + 1])
            elif re.search('[!.?]', question[k]):
                continue
            elif question[k] != '':
                question2.append(question[k])

        question = question2

        if len(question) >= 3:
            question2 = question[0] + question[-2]
            question2 += question[-1] if 'hint' not in question[-1] else ''
            questions[i] = question2

        for word in questions[i].lower().split():
            try:
                if (word_dict[word] < 0.25 or word in keywords) and word not in stopwords:
                    new_question += word + ' '
            except:
                pass
        if len(new_question):
            new_questions.append(new_question)
        print(CURSOR_UP_ONE + ERASE_LINE + 'Processed {} Questions.'.format(i + 1))

    if len(new_questions) > 0:
        json.dump(new_questions, open('resources/%s_questions_filtered.json' %textbook.lower(), 'w'))