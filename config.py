import os

basedir = os.path.dirname(__file__)

# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
# SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
ASK_VERIFY_REQUESTS = False
MONGO_URI = "mongodb://localhost:27017/Database"
UPLOAD_FOLDER = 'uploads'