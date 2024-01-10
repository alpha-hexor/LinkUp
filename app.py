from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import random
import string
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# Configure the database URI
database_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mydatabase.db')

# Configure the database URI with the absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

#various app configurations
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['UPLOAD_FOLDER'] = 'attachments'  # Folder for uploaded files
app.config['AVATARS_FOLDER'] = 'avatars' #for avatar stuff
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

socketio = SocketIO(app, logger=True, engineio_logger=True,max_http_buffer_size=40 * 1024 * 1024)

app.static_folder = 'static'

login_manager = LoginManager()
login_manager.init_app(app)

# Define the User model
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='messages')
    file_path = db.Column(db.String(200))  # Path to the uploaded file
    file_name = db.Column(db.String(100))  # Original file name

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    messages = db.relationship('ChatMessage', backref='room')

user_rooms = db.Table('user_rooms',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('room_id', db.Integer, db.ForeignKey('chat_room.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    rooms = db.relationship('ChatRoom', secondary=user_rooms, backref='users')
    profile_pic = db.Column(db.String(255))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create the database tables (only required once)
def create_db():
    with app.app_context():
        db.create_all()

# Define a route for serving uploaded files
@app.route('/avatars/<filename>')
def upload_avatar(filename):
    return send_from_directory(app.config['AVATARS_FOLDER'],filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

#various routes
@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    # Check if the username or email already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        message = "Username already exists. Please choose a different username"
        return render_template("auth.html", auth_error=message)

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        message = "Email already exists. Please choose a different email"
        return render_template("auth.html", auth_error=message)

    # Create a new user and save it to the database
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    default_pic = url_for('upload_avatar',filename='default.png')
    new_user = User(username=username, email=email, password=hashed_password,profile_pic=default_pic)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.check_password_hash(user.password, password):
            error_message = "Invalid email or password"
            return render_template("auth.html", auth_error=error_message)

        login_user(user)

        # If login is successful, then redirect to the chat
        return redirect(url_for('chat'))
    else:
        return render_template('auth.html')

@app.route("/", methods=["GET"])
def index():
    return redirect(url_for('login'))
