from __future__ import unicode_literals
from flask import Flask, flash, redirect, render_template, request, session, abort
from pymongo import MongoClient
from flask import jsonify
import os
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from hazm import *
import numpy as np

app = Flask(__name__)
#secret key
app.config['SECRET_KEY'] = '!@#@$%^&*(&*^%$#@RTYJUKHGFDRtyu8i78yujghfdrt56y@#$%^&54356'
#upload folder path
app.config['UPLOAD_FOLDER'] = 'static/uploads'

#database config
pd_db_uri = 'mongodb://localhost:27017/pl_db'
pl_db = MongoClient(pd_db_uri)
pl_db = pl_db['pl_db']
stopwords_collection = pl_db['stopwords']
papers_collection = pl_db['papers']

#---------------------#
#Loading required data#
#---------------------#

special_characters ='"#()*,-./:[]«»،؛؟٬'
stopwords = list(stopwords_collection.find({},{'word':1, '_id':False}))
stopwords = [word['word'] for word in stopwords]

#---------------------#
#Helper functions     #
#---------------------#

def get_cosine_sim(*strs):
    vectors = [t for t in get_vectors(*strs)]
    return cosine_similarity(vectors)
    
def get_vectors(*strs):
    text = [t for t in strs]
    vectorizer = CountVectorizer(text)
    vectorizer.fit(text)
    return vectorizer.transform(text).toarray()

def preprocess(str):
    str_list = word_tokenize(str)
    str_list = [word for word in str_list if word not in special_characters]
    str_list = [word for word in str_list if word not in stopwords]
    str_f = " ".join(str_list)
    if '\n' in str_f:
        str_f.replace('\n','')
    return str_f

#----------------------#
#Routes and Controllers#
#----------------------#

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/check', methods=['GET','POST'])
def check():
    source = request.args.get("source")
    text = request.args.get("text")

    source = preprocess(source)
    text = preprocess(text)

    match_value = get_cosine_sim(source, text)
    match_value = round(match_value[0][1]*100,2)

    return render_template(
        'home_result.html',
        match_value = match_value,
        source = source,
        text = text
    )

@app.route('/upload')
def upload_file_view():
   return render_template('upload.html')

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], 'file'))
        content = open(os.path.join(app.config['UPLOAD_FOLDER'], 'file'))
        content = [line for line in content]
        content = " ".join(content)
        content = preprocess(content)
        p = papers_collection.find({},{'paper':1, '_id':False})
        p_count = papers_collection.find({},{'paper':1, '_id':False}).count()
        max_match_value = np.float('-inf')
        for i in range(p_count):
            get_paper = p[i]['paper']
            match_value = get_cosine_sim(content, get_paper)
            match_value = round(match_value[0][1]*100,2)
            if match_value>max_match_value:
                max_match_value = match_value
        print(max_match_value)
        if max_match_value<50:
            file_dict = {'paper':content}
            papers_collection.insert_one(file_dict)
        return render_template(
            'file_uploaded.html',
            max_match_value = max_match_value
        )
        return 'file uploaded successfully'

@app.route('/check_api/<string:content>', methods=['GET','POST'])
def check_api(content):
    """source = request.args.get("source")
    text = request.args.get("text")

    source = preprocess(source)
    text = preprocess(text)

    match_value = get_cosine_sim(source, text)
    match_value = round(match_value[0][1]*100,2)

    return render_template(
        'home.html',
        match_value = match_value,
        source = source,
        text = text
    )"""
    result = {
        'result':content
    }
    return jsonify(result)

if __name__ == "__main__":
    app.run()




