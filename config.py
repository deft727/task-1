import os
basedir = os.path.abspath(os.path.dirname(__file__))

class MConfig :

    SECRET_KEY = '3254365h6k5g6kh7k5kjlhr5h4ouirhhh324'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'admin.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MY_KEY = 1234
    SUPERUSER = 'root'
    PICS_FOLDER = "/static/images"
