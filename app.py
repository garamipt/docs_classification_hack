from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from flask_admin import Admin
import os
import pandas as pd
from pyth.plugins.plaintext.writer import PlaintextWriter
from pyth.plugins.rtf15.reader import Rtf15Reader 
import re
import pymorphy2
from autocorrect import Speller
import numpy as np
from catboost import CatBoostClassifier
import docx
from converter import read_file


def getText(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)
def read_txt(filename):
    with open("test.txt") as f:
        text = f.read()
    return text
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

def latest_process_data(data, text_cols=['40_words']):
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
    res = words[:20] if len(words) >= 20 else words
    return " ".join(res)

def get_40_words(text):
    words = text.split()
    res = words[:40] if len(words) >= 40 else words
    return " ".join(res)

def predict(uploaded_files, use_latest=True):
    text_df = pd.DataFrame({"class": [], "text": []})
    i = 0
    for uploaded_file in uploaded_files:
        if uploaded_file.filename.split(".")[1] == "rtf":
            try:
                text_df.loc[i] = ["unknown", parse_rtf("uploads/" + uploaded_file.filename)]
            except:
                try:
                    text_df.loc[i] = ["unknown", read_file("uploads/" + uploaded_file.filename)]
                except:
                    text_df.loc[i] = ["unknown", "Договор"]
        elif uploaded_file.filename.split(".")[1] == "docx":
            text_df.loc[i] = ["unknown", getText("uploads/" + uploaded_file.filename)]
        elif uploaded_file.filename.split(".")[1] == "txt":
            text_df.loc[i] = ["unknown", read_txt("uploads/" + uploaded_file.filename)]
        else:
            try:
                text_df.loc[i] = ["unknown", read_file("uploads/" + uploaded_file.filename)]
            except:
                text_df.loc[i] = ["unknown", "Договор"]
        i += 1

    if use_latest:
        text_df["40_words"] = text_df["text"].apply(get_40_words)
    else:
        text_df["20_words"] = text_df["text"].apply(get_20_words)

    if use_latest:
        text_df = text_df.drop(columns=['text'])

        data, _ = latest_process_data(text_df)
        data_2 = data
        added_words = ['иск', 'накладная', 'акт', 'акт проверки', 
                       'инн', 'огрн', 'бик', 'покупатель', 
                        'счет-оферта', 'счет', 'расторжение', 
                        'услуга','трудовой', 'заявка', 'исполнение', 
                        'поручение', 'правила', 'правило', 'покупка', 
                        "продажа", 'купля', 'купля-продажа', 
                        'купли-продажи', 'неустойка', 'возмещение', 
                        'указ', 'кодекс', 'раздел', 'общество', 'приказ', 
                        'приказываю', 'оказание', 'решение', 'собрание', 
                        'федеральный', 'письмо', 'ооо', 'оао', 'индивидуальный',
                        'уполномочивать', 'доверенность на', 'доверяю']
    else:
        data, _ = process_data(text_df)
        data_2, _ = process_data(data, ['20_words'])

    uniq_lemm_classes = np.array(['соглашение', 'заявление', 'доверенность', 'договор', 'акт',
       'приказ', 'решение', 'устав', 'договор оферты', 'счет',
       'приложение'])
    
    if use_latest:
        data_2[f'count_соглашение'] = data_2['lemm_40_words'].apply(lambda x: x.count("соглашение"))
        for i in (list(uniq_lemm_classes) + added_words)[1:]:
            data_2[f'count_{i}'] = data_2['lemm_40_words'].str.count(rf'\b{i}\b')
        data_2[f'count_оферта'] = data_2['lemm_40_words'].apply(lambda x: x.count("оферта"))
        data_2[f'count_оферта'] = data_2['lemm_40_words'].apply(lambda x: x.count("офферта"))
        data_2[f'count_исполнитель'] = data_2['lemm_40_words'].apply(lambda x: x.count("исполнитель"))
        data_2[f'count_подрядчик'] = data_2['lemm_40_words'].apply(lambda x: x.count("подрядчик"))
        data_2[f'count_заказчик'] = data_2['lemm_40_words'].apply(lambda x: x.count("заказчик"))
        data_2[f'count_поручитель'] = data_2['lemm_40_words'].apply(lambda x: x.count("поручитель"))
    else:
        data_2[f'count_соглашение'] = data_2['lemm_20_words'].apply(lambda x: x.count("соглашение"))
        for i in uniq_lemm_classes[1:]:
            data_2[f'count_{i}'] = data_2['lemm_20_words'].str.count(rf'\b{i}\b')

    if use_latest:
        del data_2['40_words']
    else:
        del data_2['text']
        del data_2['20_words']
        
    if use_latest:
        X_val = data_2.drop(columns=['class', data_2.columns[0]])
    else:
        X_val = data_2.drop(columns=['lemm_text', 'class', data_2.columns[0]])

    catboss = CatBoostClassifier()
    catboss.load_model('catbossv5_final' if use_latest else "catbossv1")
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
    
@app.route("/index")
def index_2():
    wrong_docs = request.args.get("wrong_docs")
    return render_template("index.html", wrong_docs = wrong_docs)


@app.route("/upload", methods=["POST"])
def upload():
    sets = [set(["contract", "act", "order"]), set(["arrangement"]), set(["application", "act", "order", "arrangement"])]
    print(request.form["service"] == "4")
    if request.form["service"] == "4":
        return redirect(url_for("index", wrong_docs=4))
    service = int(request.form["service"])
    uploaded_files = request.files.getlist("files")
    # if len(uploaded_files) != service:
    #     return redirect(url_for("", wrong_docs="True"))
    for file_one in uploaded_files:
        file_one.save(os.path.join(app.config['UPLOAD_FOLDER'], file_one.filename))
    # mongo.save_file(uploaded_files.filename, uploaded_files)
    predicted = predict(uploaded_files)
    print(predicted)
    print(set(predicted))
    print(sets[service])
    if set(predicted) != sets[service]:
        return redirect(url_for("index", wrong_docs=True))
    return redirect(url_for("success", uploaded_files=",".join([class_one for class_one in predicted]), filenames=','.join([uploaded_file.filename for uploaded_file in uploaded_files])))
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
