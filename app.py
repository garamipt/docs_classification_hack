from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from flask_admin import Admin
import os
import os
import pandas as pd
from pyth.plugins.plaintext.writer import PlaintextWriter
from pyth.plugins.rtf15.reader import Rtf15Reader 
import re
import pymorphy2
from autocorrect import Speller
import spacy
import pandas as pd
import numpy as np
from catboost import Pool, CatBoostClassifier
import docx

def getText(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)

spell = Speller("ru")
morph = pymorphy2.MorphAnalyzer()

def process_data(data, text_cols=['text']):
    new_text_cols = [f'lemm_{text_col}' for text_col in text_cols] + text_cols
    for text_col in text_cols:
        data[text_col] = data[
            text_col
        ].apply(remove_control_symbols)
        
        data[text_col] = data[
            text_col
        ].str.replace("[\(\[].*?[\)\]]", "", regex=True)

        data.loc[:, f"lemm_{text_col}"] = data.apply(
            lambda x: lemmatize(spell(x[text_col])), axis=1
        )
    return data, new_text_cols

    
def lemmatize(text) -> str:
    words = text.split()
    res = list()
    for word in words:
        p = morph.parse(word)[0]
        res.append(p.normal_form)
    return " ".join(res)


def remove_control_symbols(text):
    # Регулярное выражение для поиска всех CR (перевод каретки), LF (переход на новую строку)
    # и TAB (табуляция) символов, а также одного или более пробелов
    pattern = re.compile(r'[\r\n\t\b]+')
    
    # Заменяем найденные совпадения на пробел, тем самым удаляя их
    return pattern.sub(' ', text)

def parse_rtf(file_path): 
    # Read the RTF file 
    doc = Rtf15Reader.read(open(file_path, "rb")) 
 
    # Extract plain text from the document 
    text = PlaintextWriter.write(doc).getvalue() 
     
    return text 

def get_20_words(text):
    words = text.split()
    return " ".join(words[:20])

def predict(uploaded_files):
    text_df = pd.DataFrame({"class": [], "text": []})
    i = 0
    for uploaded_file in uploaded_files:
        if uploaded_file.filename.split(".")[1] == "rtf":
            try:
                text_df.loc[i] = ["unknown", parse_rtf("uploads/" + uploaded_file.filename)]
            except:
                text_df.loc[i] = ["unknown", "Договор"]
        elif uploaded_file.filename.split(".")[1] == "docx":
            text_df.loc[i] = ["unknown", getText("uploads/" + uploaded_file.filename)]
        i += 1
    text_df["20_words"] = text_df["text"].apply(get_20_words)
    data, _ = process_data(text_df)
    data_2, short_text = process_data(data, ['20_words'])
    uniq_lemm_classes = np.array(['соглашение', 'заявление', 'доверенность', 'договор', 'акт',
       'приказ', 'решение', 'устав', 'договор оферты', 'счет',
       'приложение'])
    data_2[f'count_соглашение'] = data_2['lemm_20_words'].apply(lambda x: x.count("соглашение"))
    for i in uniq_lemm_classes[1:]:
        data_2[f'count_{i}'] = data_2['lemm_20_words'].str.count(rf'\b{i}\b')
    del data_2['text']
    del data_2['20_words']
    X_val = data_2.drop(columns=['lemm_text', 'class', data_2.columns[0]])
    X_val.to_csv("prepared.csv")
    catboss = CatBoostClassifier()
    catboss.load_model("catbossv1")
    y_pred = catboss.predict(X_val)
    return [i[0] for i in y_pred]


app = Flask(__name__, static_folder='static', static_url_path='')

app.config.from_object('config')
app.secret_key = 'super secret key'

mongo = PyMongo(app)

admin = Admin(app=app, name='Admin', url='/admin', template_mode='bootstrap4')

@app.route("/")
def index():
    wrong_docs = request.args.get("wrong_docs")
    return render_template("index.html", wrong_docs = wrong_docs)


@app.route("/upload", methods=["POST"])
def upload():
    service = request.form["service"]
    uploaded_files = request.files.getlist("files")
    # if len(uploaded_files) != service:
    #     return redirect(url_for("", wrong_docs="True"))
    for file_one in uploaded_files:
        file_one.save(os.path.join(app.config['UPLOAD_FOLDER'], file_one.filename))
    # mongo.save_file(uploaded_files.filename, uploaded_files)
    return redirect(url_for("success", uploaded_files=",".join([class_one for class_one in predict(uploaded_files)]), filenames=','.join([uploaded_file.filename for uploaded_file in uploaded_files])))
    # return render_template("file_uploaded.html", file_name=uploaded_file.filename)

@app.route("/success")
def success():
    uploaded_files = request.args.get("uploaded_files")
    filenames = request.args.get("filenames")
    return render_template("file_uploaded.html", zipped=zip(uploaded_files.split(','), filenames.split(',')))

@app.route("/team")
def team():
    return render_template("team.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000, debug=True)
    # from waitress import serve

    # serve(app, host="192.168.68.100", port=7776)
