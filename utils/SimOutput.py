
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.decomposition import TruncatedSVD
import csv
import re
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from scipy.spatial.distance import cosine

from os import listdir
import os
import utils.GlobalVar as gl
from utils.GetCSV import getCsvByfilePath









def LatentSemanticAnalysis(ProjectDataPath,UDPath, UDPParseFlag):
    FilePath = pd.read_csv(ProjectDataPath + "-filename.csv", names=["path"])
    filenames = FilePath["path"].values

    count=0
    if UDPParseFlag:
        for file_path in filenames:
            
            count += 1
            print(count)
            # if count < 324:
            #     continue
            getCsvByfilePath(UDPath, file_path)

    if os.path.exists(ProjectDataPath +"-svd.csv"):
        svdMatrix = pd.read_csv(ProjectDataPath +"-svd.csv", header=None)
    else:
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
                
                file_to_str = file_to_str.lower()
                text_list = re.sub("[^a-zA-Z]", " ", file_to_str).split()
                english_punctuations = [',', '.', ':', ';', '?', '(', ')', '[', ']', '&', '!', '*', '@', '#', '$', '%', '"',
                                        '//*',
                                        '*//']
                text_list = [word for word in text_list if word not in english_punctuations]
                
                stops = set(stopwords.words("english"))
                text_list = [word for word in text_list if word not in stops]
                str_text = ""
                for list in text_list:
                    str_text += ' ' + list
                    
                
                
                
                
                
                documents.append(str_text)
                
            
            
        
        

        
        
        cv = CountVectorizer(input=documents, strip_accents='ascii')
        dtMatrix = cv.fit_transform(filenames).toarray()
        
        featurenames = cv.get_feature_names_out()
        

        
        tfidf = TfidfTransformer()
        tfidfMatrix = tfidf.fit_transform(dtMatrix).toarray()
        

        
        
        
        svd = TruncatedSVD(n_components=100)
        svdMatrix = svd.fit_transform(tfidfMatrix)
        svdMatrix=np.around(svdMatrix, 2)
        svdMatrix = pd.DataFrame(svdMatrix)
        
        svdMatrix.to_csv(ProjectDataPath+ "-svd.csv", header=None, index=False)

    
    cos = cosine_similarity(svdMatrix)
    
    cos = np.around(cos, 2)
    cos=pd.DataFrame(cos)
    cos.to_csv(ProjectDataPath +"-seMatrix.csv", header=None, index=False)
    return cos
