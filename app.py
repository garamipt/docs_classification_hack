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
    return redirect(url_for("success", uploaded_files=",".join([file_one.filename for file_one in uploaded_files])))
    # return render_template("file_uploaded.html", file_name=uploaded_file.filename)

@app.route("/success")
def success():
    uploaded_files = request.args.get("uploaded_files")
    return render_template("file_uploaded.html", file_name=uploaded_files)

@app.route("/team")
def team():
    return render_template("team.html")

if __name__ == "__main__":
    from waitress import serve

    serve(app, host="192.168.68.100", port=7776)
