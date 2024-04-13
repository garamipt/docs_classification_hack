from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from flask_admin import Admin
import os

app = Flask(__name__, static_folder='static', static_url_path='')

app.config.from_object('config')
app.secret_key = 'super secret key'

mongo = PyMongo(app)

admin = Admin(app=app, name='Admin', url='/admin', template_mode='bootstrap4')

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    print(0)
    uploaded_files = request.files.getlist("files")
    for file_one in uploaded_files:
        file_one.save(os.path.join(app.config['UPLOAD_FOLDER'], file_one.filename))
    # mongo.save_file(uploaded_files.filename, uploaded_files)
    return redirect(url_for("success", uploaded_files=",".join([file_one.filename for file_one in uploaded_files])))
    # return render_template("file_uploaded.html", file_name=uploaded_file.filename)

@app.route("/success")
def success():
    uploaded_files = request.args.get("uploaded_files")
    return render_template("file_uploaded.html", file_name=uploaded_files)

app.run(host='0.0.0.0',port=5000, debug=True)