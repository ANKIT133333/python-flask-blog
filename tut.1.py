from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message 
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import math
from datetime import datetime

# Load configuration
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
# app.secret_key = "super-secret-key"
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')  # Secure secret key for session management



# Email configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME', 'yadavankit37040@gmail.com'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', 'uedqrosuvefcbmpw'),
)

mail = Mail(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri'] if local_server else params['prod_uri']
db = SQLAlchemy(app)

# -------------------- Database Models --------------------

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12))
    img_file = db.Column(db.String(12))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# -------------------- Routes --------------------
# ============= home
@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)



@app.route("/post/<string:post_slug>", methods=['GET'])
def view_post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)


# ============= about
@app.route("/about")
def about():
    return render_template('about.html', params=params)



# ============= dashboard 

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    # Check if user is already logged in
    if 'user' in session and session['user'] == params['admin_email']:
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    # Handle login form
    if request.method == 'POST':
        username = request.form.get('email')
        password = request.form.get('password')

        if username == params['admin_email'] and password == params['admin_password']:
            session['user'] = username
            flash('Welcome to the Dashboard!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to prevent form re-submission
        else:
            flash('Invalid credentials', 'danger')
            return render_template('login.html', params=params)

    # Show login page on GET request
    return render_template('login.html', params=params)

# edit post
@app.route("/edit/<string:sno>" , methods=['GET', 'POST'])
def edit(sno):
    if "user" in session and session['user']==params['admin_user']:
        if request.method=="POST":
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
        
        if sno=='0':
            post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
            db.session.add(post)
            db.session.commit()
        else:
            post = Posts.query.filter_by(sno=sno).first()
            post.box_title = box_title
            post.tline = tline
            post.slug = slug
            post.content = content
            post.img_file = img_file
            post.date = date
            db.session.commit()
            return redirect('/edit/'+sno)

    post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post)


# delete post
@app.route("/delete/<string:sno>" , methods=['GET', 'POST'])
def delete(sno):
    if "user" in session and session['user']==params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")



# ============= contact
@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name=name, phone_num=phone, msg=message, email=email)
        db.session.add(entry)
        db.session.commit()

        try:
            mail.send_message(
                subject=f"New message from {name}",
                sender=app.config['MAIL_USERNAME'],
                recipients=[params['gmail_user']],  # Admin email from config
                body=f"Message: {message}\nPhone: {phone}\nFrom: {name}\nEmail: {email}"
            )
            flash("Thanks for your message! We will get back to you soon.", "success")
        except Exception as e:
            flash(f"Error sending message: {str(e)}", "danger")

    return render_template('contact.html', params=params)


# ============= post
@app.route("/post/<string:post_slug>", methods=['GET' ,'POST'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)

# ============= login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # First try database authentication
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        # If database auth fails, try config file auth as fallback
        elif email == params['admin_email'] and password == params['admin_password']:
            session['user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'danger')
    return render_template('login.html', params=params)


# ============= logout

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))


# -------------------- Main --------------------

if __name__ == '__main__':
    app.run(debug=True)
