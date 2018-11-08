from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:password@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] =  True
db = SQLAlchemy(app)
app.secret_key = 'abcdefg'

class Blog(db.Model): 

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(120))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

tasks = []

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'register']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['email'] = email
            flash("Logged in")
            return redirect('/blog')
        else:
            flash("User password incorrect or user does not exist", 'error')

    return render_template('login.html')

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        #TODO - validate data

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/blog')
        else:
            #TODO - better response message
            return "<h1>Duplicate user</h1>"

    return render_template('register.html')

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/blog')

@app.route('/blog', methods=['POST', 'GET'])
def index():
    blog_id = request.args.get("id")
    owner = User.query.filter_by(email=session['email']).first()

    if blog_id:
        blog = Blog.query.filter_by(id=blog_id).first()
        return render_template('blog.html',title=blog.title,
         blog=blog)

    blogs = Blog.query.filter_by(owner=owner).all()
    return render_template('blogs.html',title="Build a Blog",
         blogs=blogs)

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    owner = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        blog_name = request.form['title']
        blog_body = request.form['body']
        error = False
        if not blog_name:
            flash("Please enter a blog title", 'title-error')
            error = True
        if not blog_body:
            flash("Please enter a blog post", 'post-error')
            error = True
        if error:
            return redirect('/newpost')

        new_blog = Blog(blog_name, blog_body, owner)
        db.session.add(new_blog)
        db.session.commit()
        return redirect('/blog?id=' + str(new_blog.id))

    return render_template('newpost.html',title="Add a Blog Post")

if __name__ == '__main__':
    app.run()