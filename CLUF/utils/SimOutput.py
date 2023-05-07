import csv
import math
import multiprocessing
import re

import gensim
import numpy as np
import pandas as pd
from gensim.models.doc2vec import TaggedDocument
from gensim.models import KeyedVectors as word2vec
from nltk import word_tokenize
from nltk.corpus import stopwords
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
from spiral import ronin

from utils.GlobalVarUpdate import *
from utils.GetCSV import getCsvByfilePath


def UDPFileParse(version_middle_path, UDPath):
    FilePath = pd.read_csv(version_middle_path + "-filename.csv", names=["path"])
    filenames = FilePath["path"].values

    count = 0

    for file_path in filenames:
        count += 1
        print(count)
        getCsvByfilePath(UDPath, file_path)


def get_document(version_middle_path):

    FilePath = pd.read_csv(version_middle_path + "-filename.csv", names=["path"])
    filenames = FilePath["path"].values

    documents = []

    for file in filenames:
        with open(file + '.csv', 'r', encoding='utf8') as file_name:
            file_content = csv.reader(file_name)
            file_to_str = ""
            clear_flag = -2
            for content in file_content:
                if clear_flag < 0:
                    clear_flag += 1
                    continue
                if (content[1] == "Comment" or content[1] == "Identifier"):
                    file_to_str += " " + content[0]

            text_list = re.sub("[^a-zA-Z]", " ", file_to_str).split()
            english_punctuations = [',', '.', ':', ';', '?', '(', ')', '[', ']', '&', '!', '*', '@', '#', '$', '%', '"',
                                    '//*',
                                    '*//']
            text_list = [word for word in text_list if word not in english_punctuations]

            stops = set(stopwords.words("english"))
            text_list = [word for word in text_list if word not in stops]
            text_list = [word.lower() for word in text_list if (word.isalpha() and len(word) > 1) or (word.isnumeric())]

            str_text = ""
            for list in text_list:
                str_text += ' ' + list

            documents.append(str_text)

    return documents


def get_tfidf_vector(documents, version_middle_path):
    FilePath = pd.read_csv(version_middle_path + "-filename.csv", names=["path"])
    filenames = FilePath["path"].values

    cv = CountVectorizer(input=documents, strip_accents='ascii')
    dtMatrix = cv.fit_transform(filenames).toarray()

    tfidf = TfidfTransformer()
    tfidfMatrix = tfidf.fit_transform(dtMatrix).toarray()
    return tfidfMatrix


def go_through_LSA(ProjectDataPath, se_embeddings, vectorize_type):
    n_comps = min(se_embeddings.shape) // 2 + 1
    svd = TruncatedSVD(n_components=100, algorithm="arpack")
    # svdMatrix = svd.fit_transform(tfidfMatrix)
    svdMatrix = svd.fit_transform(se_embeddings)
    svdMatrix = np.around(svdMatrix, 2)
    svdMatrix = pd.DataFrame(svdMatrix)
    # print('svdMatrix\n',svdMatrix)
    # svdMatrix.to_csv("svd"+".csv", header=None, index=False)
    svdMatrix.to_csv(ProjectDataPath + "-svd-" + vectorize_type + ".csv", header=None, index=False)
    return svdMatrix


def get_d2v_vector(documents):
    tagged_data = [TaggedDocument(words=word_tokenize(_d.lower()), tags=[str(i)]) for i, _d in enumerate(documents)]
    vec_size = 100
    alpha = 0.045
    model = gensim.models.Doc2Vec(dm=1, vector_size=vec_size, negative=5,
                                  hs=0, min_count=2, sample=0, workers=multiprocessing.cpu_count(),
                                  alpha=alpha, min_alpha=alpha / 3)
    model.build_vocab(tagged_data)
    model.train(tagged_data, total_examples=model.corpus_count, epochs=model.epochs)

    return model


def get_c2v_vector(model, splited_words):
    sentences_matrix = []
    index = 0
    while index < len(splited_words):
        words_matrix = []
        words = splited_words[index].split(" ")
        for word in words:
            if word in model:
                words_matrix.append(np.array(model[word]))
        feature = averageVector(many_vectors=words_matrix,
                                column_num=model.vector_size)
        sentences_matrix.append(feature)
        index += 1
    return sentences_matrix


def averageVector(many_vectors, column_num):
    average_vector = []
    for i in range(0, column_num, 1):
        average_vector.append(0)
    row_num = len(many_vectors)
    row_index = 0
    for weight_index, vector in enumerate(many_vectors):
        for i in range(0, column_num, 1):
            average_vector[i] += float(vector[i])
        row_index += 1
    for i in range(0, column_num, 1):
        average_vector[i] = average_vector[i] / row_num
    return average_vector

def code_stem(documents):
    stemmed_documents=[]
    for doc in documents:
        word_list=doc.split(' ')
        stemmed_doc=[]
        for word in word_list:
            stemmed_doc.extend(ronin.split(word))
        stemmed_doc=' '.join(stemmed_doc)
        stemmed_documents.append(stemmed_doc)
    return stemmed_documents

def train_idf(doc_list):
    idf_dic = {}
    tt_count = len(doc_list)

    for doc in doc_list:
        for word in set(doc):
            idf_dic[word] = idf_dic.get(word, 0.0) + 1.0

    for k, v in idf_dic.items():
        idf_dic[k] = math.log(tt_count / (1.0 + v))

    print("tt_count" + str(tt_count))
    default_idf = math.log(tt_count / (1.0))
    return idf_dic, default_idf

def get_c2v_tfidf_vector(model,idf_dic,default_idf, splited_words):
    sentences_matrix = []
    index = 0

    while index < len(splited_words):
        words_matrix = []
        word_weight = []
        words = splited_words[index].split(" ")
        for word in words:
            if word in model:
                words_matrix.append(np.array(model[word]))
                if word in idf_dic:
                    word_weight.append(idf_dic[word])
                else:
                    word_weight.append(default_idf)

        feature = averageVector_tfidf(many_vectors=words_matrix, vector_weight=word_weight,
                                column_num=model.vector_size)
        sentences_matrix.append(feature)
        index += 1
    return sentences_matrix


def averageVector_tfidf(many_vectors, vector_weight, column_num):
    average_vector = []
    for i in range(0, column_num, 1):
        average_vector.append(0)
    row_num = len(many_vectors)
    row_index = 0
    for weight_index, vector in enumerate(many_vectors):
        for i in range(0, column_num, 1):
            average_vector[i] += float(vector[i]) * vector_weight[weight_index]
        row_index += 1
    for i in range(0, column_num, 1):
        average_vector[i] = average_vector[i] / row_num
    return average_vector

def GetSematicEntrance(version_middle_path, vectorize_type):
    # if os.path.exists(ProjectDataPath + "-svd-" + vectorize_type + ".csv"):
    #     svdMatrix = pd.read_csv(ProjectDataPath + "-svd-" + vectorize_type + ".csv", header=None)
    # #
    # else:
    documents = get_document(version_middle_path)
    # print(documents)
    if vectorize_type == 'c2v_tfidf':
        stemmed_documents = code_stem(documents)
        doc_list = [doc.split() for doc in stemmed_documents]
        idf_dic, default_idf = train_idf(doc_list)
        vectors_text_path = gl.input_data_path+r'\c2v_token_vecs\token_vecs.txt'  # or: `models/java14_model/tokens.txt'
        # vectors_text_path = r'D:\program\code2vec\token_vecs\token_vecs.txt'  # or: `models/java14_model/tokens.txt'
        model = word2vec.load_word2vec_format(vectors_text_path, binary=False)
        vectors = get_c2v_tfidf_vector(model, idf_dic, default_idf, stemmed_documents)
        # cos = cosine_similarity(matrix)

    cos = cosine_similarity(vectors)
    cos = np.around(cos, 2)
    cos = pd.DataFrame(cos)
    cos.to_csv(version_middle_path + "-seMatrix-" + vectorize_type + ".csv", header=False, index=False)
    return cos
