from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
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

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup','list_blogs','index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if user.password == password:
                session['username'] = username
                flash("Logged in")
                return redirect('/newpost')
            else:
                flash("Incorrect password", 'pw-error')
        else:
            flash("User does not exist", 'user-error')

    return render_template('login.html')

@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        if username and password and verify:
            if len(username) > 2:
                existing_user = User.query.filter_by(username=username).first()
                if not existing_user:
                    if len(password) > 2:
                        if password == verify:
                            new_user = User(username, password)
                            db.session.add(new_user)
                            db.session.commit()
                            session['username'] = username
                            return redirect('/newpost')
                        else:
                            flash("Passwords do not match","pw-error")
                    else:
                        flash("Password must be at least 3 characters long","pw-error")
                else:
                    flash("Username already taken", 'user-error')
            else:
                flash("Username must be at least 3 characters long", "user-error")
        else: 
            flash("Please fill out all form fields", "pw-error")

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html',users=users)

@app.route('/blog', methods=['POST', 'GET'])
def list_blogs():
    blog_id = request.args.get("blog_id")
    user_id = request.args.get("user_id")
    show_session_posts = request.args.get("user_posts")
    if blog_id:
        blog = Blog.query.filter_by(id=blog_id).first()
        return render_template('blog.html',title=blog.title,
         blog=blog)

    if show_session_posts:
        owner = User.query.filter_by(username=session['username']).first()
        blogs = Blog.query.filter_by(owner=owner).all()
    elif user_id:
        blogs = Blog.query.filter_by(owner_id=user_id).all()
    else:
        blogs = Blog.query.all()
    return render_template('blogs.html',title="Build a Blog",
         blogs=blogs)

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    owner = User.query.filter_by(username=session['username']).first()

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