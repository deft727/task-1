from flask import Flask, render_template, request, redirect, flash, url_for, session 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField, BooleanField,ValidationError,FileField,SelectField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, Email, EqualTo
from datetime import datetime,timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, current_user, logout_user, login_required,UserMixin
from os.path import join, dirname, realpath
from config import MConfig
from PIL import Image
import PIL
from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
import random

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = "static/images/"
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config.from_object(MConfig)
db = SQLAlchemy(app)
admin = Admin(app)
migrate=Migrate(app, db)
manager=Manager(app)
manager.add_command('db',MigrateCommand)

class Article(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    Authors=db.Column(db.String(50), nullable = False)
    Header=db.Column(db.String(300), nullable = False)
    content = db.Column(db.String(1500), nullable = False)
    img1=db.Column(db.String(248), nullable=True)
    creationData=db.Column(db.DateTime,default=datetime.now())
    tagi= db.relationship('Tag',backref='tags',lazy='dynamic')
    def __repr__(self) :
        return f'<Blog{self.content}>'

class Tag(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    postId=db.Column(db.Integer,  db.ForeignKey('article.id'))


    def __repr__(self) :
        return f'<Tag{self.postId}>'


class Users(db.Model, UserMixin):
    __tablename__ = 'Users'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50), nullable = False)
    email=db.Column(db.String(50), nullable = False)
    password = db.Column(db.String(250), nullable = False)
    creationData=db.Column(db.DateTime,default=datetime.now())
    def __repr__(self) :
        return f'<Users{self.content}>'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
    
@app.errorhandler(404)
def page_not_found(error):
    return redirect ('/')

@app.errorhandler(500)
def server_error(error):
    return redirect ('/')

admin.add_view(ModelView(Users,db.session))
admin.add_view(ModelView(Article,db.session))
admin.add_view(ModelView(Tag,db.session))

class ArticleForm(FlaskForm):
    Header=StringField('заголовок', validators=[DataRequired()])
    img1=  FileField()
    # img_name1=StringField('img name 1')
    Content =StringField(u'статья', widget=TextArea(),validators=[DataRequired()])
    Btm = SubmitField('Добавить')
    def validate_Content(self, field) :
        if len(field.data) < 20 :
            raise ValidationError('Article must be from 20 characters')

class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    password2 = PasswordField('password2', validators=[ DataRequired(), EqualTo('password')])
    remember_me = BooleanField('remember Me')
    submit = SubmitField('sign In')


class RegisterForm(FlaskForm) :
    username = StringField('USERNAME', validators=[ DataRequired() ])
    email = StringField('EMAIL', validators=[ Email() ])
    password1 = StringField('PASSWORD', validators=[ DataRequired() ])
    password2 = StringField('PASSWORD AGAIN', validators=[ DataRequired(), EqualTo('password1') ])

    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username already exists')
    
    def validate_password(self, password):
        x=len(str(password.data))
        if x<4:
            raise ValidationError('4 characters minimum')

@app.route('/')
def index():
    sort = request.args.get('sort')
    page=request.args.get('page')
    
    articles = Article.query.order_by(Article.creationData.desc())

    if sort is not None:
        if sort == '1':
            articles = Article.query.order_by(Article.creationData)
        elif sort == '2':
            articles = Article.query.order_by(Article.creationData.desc())

    if page and page.isdigit():
        page=int(page)
    else:
        page=1

    pages=articles.paginate(page=page,per_page=10)
    return render_template('index.html',articles=articles,pages =pages)

@app.route('/post_tag/<tag>', methods=['GET','POST'])
def tag(tag):
    if tag:
        articles= Tag.query.filter(Tag.name==tag).all()
        return  render_template('post_tag.html',tags=articles)
    return  render_template('post_tag.html')


@app.route('/show', methods=['GET'])
def show():

    artId = request.args.get('id')
    tags=Tag.query.filter_by(postId=artId).all()

    text = Article.query.filter_by(id=artId).first()
    return render_template('show.html',art=text,tags=tags)

@app.route('/register', methods=[ 'GET', 'POST' ])
def register() :
    reg = RegisterForm()
    # time=datetime.now()
    if current_user.is_authenticated:
        redirect(url_for('index'))
    if reg.validate_on_submit():
        user=reg.username.data
        email=reg.email.data
        password1=reg.password1.data
        # print(password1)
        #password = bcrypt.hashpw(b"reg.password1.data", bcrypt.gensalt(14))
        password=generate_password_hash(password1)
        usersData=Users(username=user,email=email,password=password)#creationData=time
        db.session.add(usersData)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html', regform = reg,title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():

    form=LoginForm()
    if form.validate_on_submit():
        user = form.username.data
        password=form.password.data
        user = Users.query.filter_by(username=user).first()
        if user is None:
            flash('username is incorrect')
            return redirect('login')
        if check_password_hash(user.password, password) is False:
            flash('password is wrong')
        if check_password_hash(user.password, password)  is True:
            login_user(user, duration=timedelta(days=5))
            next_page = request.args.get('next')
            if next_page is None:
                next_page='/'
            return redirect (next_page)

    return render_template('login.html', title='Login', form=form)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = ArticleForm()
    Header=request.form.get('Header')
    Authors=current_user.username
    Content= request.form.get('Content')
    img=form.img1.data
    tags=['flask','python','web']
    tag=random.choice(tags)
    if img:
        name=img.filename
        image = Image.open(img)
        size=480,480
        image = image.resize(size)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], name))

    if form.validate_on_submit():
        article = Article(Authors=Authors, Header=Header, content=Content, img1=name)
        db.session.add(article)
        db.session.commit()
        tag=Tag(name=tag,postId=article.id)
        db.session.add(tag)
        db.session.commit()
        return redirect('/')
    return render_template('add.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    #app.run()
    app.run(debug=True)