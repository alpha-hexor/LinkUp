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

