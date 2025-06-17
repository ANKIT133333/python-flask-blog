from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
import os
from datetime import datetime

# Load configuration
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)

# Configuration
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'your-secret-key-change-this'),
    SQLALCHEMY_DATABASE_URI=params['local_uri'],
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)

# Initialize extensions
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=False)
    img_file = db.Column(db.String(12))

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in first.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route("/")
def home():
    posts = Posts.query.limit(params['no_of_posts']).all()
    return render_template('index.html', params=params, posts=posts)

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html', params=params)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            # First try database authentication
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user'] = email
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            
            # If database auth fails, try config file auth as fallback
            elif email == params['admin_user'] and password == params['admin_password']:
                session['user'] = email
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            
            flash('Invalid email or password', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            app.logger.error(f'Login error: {str(e)}')
    
    return render_template('login.html', params=params)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            message = request.form.get('message')

            entry = Contacts(name=name, phone_num=phone, msg=message, email=email)
            db.session.add(entry)
            db.session.commit()
            flash("Message sent successfully!", "success")
        except Exception as e:
            flash(f"Error sending message: {str(e)}", "danger")
            db.session.rollback()

    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first_or_404()
    return render_template('post.html', params=params, post=post)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', params=params), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html', params=params), 500

# Create tables
def init_db():
    with app.app_context():
        try:
            db.create_all()
            # Check if admin user exists
            admin = User.query.filter_by(email=params['admin_user']).first()
            if not admin:
                admin = User(
                    email=params['admin_user'],
                    password=generate_password_hash(params['admin_password'])
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully!")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")

if __name__ == '__main__':
    init_db()  # Initialize database and create admin user
    app.run(debug=True)