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
    uploaded_file = request.files["file"]
    uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename))
    mongo.save_file(uploaded_file.filename, uploaded_file)
    return redirect(url_for("success", uploaded_file=uploaded_file.filename))
    # return render_template("file_uploaded.html", file_name=uploaded_file.filename)

@app.route("/success")
def success():
    uploaded_file = request.args.get("uploaded_file")
    return render_template("file_uploaded.html", file_name=uploaded_file)

app.run(host='0.0.0.0',port=5000, debug=True)