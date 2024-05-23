from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, render_template_string,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import random
import string
from flask_bcrypt import Bcrypt
from Crypto.PublicKey import RSA
import uuid
from Crypto.Cipher import PKCS1_OAEP
from engineio.payload import Payload
Payload.max_decode_packets = 200

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

_users_in_room = {} # stores room wise user list
_room_of_sid = {} # stores room joined by an used
_name_of_sid = {} # stores display name of users



# Define the User model
class ChatMessage(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    content = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    room_id = db.Column(db.String(80), db.ForeignKey('chat_room.id'))
    user_id = db.Column(db.String(80), db.ForeignKey('user.id'))
    user = db.relationship('User', backref='messages')
    file_path = db.Column(db.String(200))  # Path to the uploaded file
    file_name = db.Column(db.String(100))  # Original file name


class ChatRoom(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    rsa_public_key = db.Column(db.Text, nullable=False)
    rsa_private_key = db.Column(db.Text, nullable=False)
    messages = db.relationship('ChatMessage', backref='room')
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class JoinRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    room_id = db.Column(db.String(80), db.ForeignKey('chat_room.id'))
    user = db.relationship('User', backref=db.backref('join_requests', cascade='all, delete-orphan'))
    room = db.relationship('ChatRoom', backref=db.backref('join_requests', cascade='all, delete-orphan'))

user_rooms = db.Table('user_rooms',
    db.Column('user_id', db.String(80), db.ForeignKey('user.id')),
    db.Column('room_id', db.String(80), db.ForeignKey('chat_room.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.String(80), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    rooms = db.relationship('ChatRoom', secondary=user_rooms, backref='users')
    profile_pic = db.Column(db.String(255))

def create_id():
    return str(uuid.uuid4())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

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
    new_user = User(id = create_id(),username=username, email=email, password=hashed_password,profile_pic=default_pic)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('verification'))

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
    
@app.route("/verification",methods=["GET","POST"])
def verification():
    if request.method == "POST":
        print("Hello world")
        return redirect(url_for('login'))
    else:
        return render_template('verification.html')

@app.route("/", methods=["GET"])
def index():
    return redirect(url_for('login'))

@app.route("/chat", methods=["GET"])
@login_required
def chat():
    return render_template("chat.html", message='')


# Room stuff
@app.route("/create_room", methods=["POST"])
@login_required
def create_room():
    room_name = request.form.get("room_name")

    # Check if the room name already exists
    existing_room = ChatRoom.query.filter_by(name=room_name).first()
    if existing_room:
        return render_template('chat.html', message="Error: room already exists")
    
    key = RSA.generate(2048)
    private_key = key.export_key(format='PEM', pkcs=8).decode('utf-8')
    public_key = key.publickey().export_key().decode('utf-8')

    new_room = ChatRoom(id = create_id(),name=room_name,rsa_public_key=public_key,rsa_private_key=private_key,admin_id=current_user.id)
    db.session.add(new_room)
    current_user.rooms.append(new_room)  # Associate the current user with the room
    db.session.commit()

    return render_template('chat.html', message="Success: room created successfully")

@app.route("/request_join", methods=["POST"])
@login_required
def request_join():
    room_name = request.form.get("room_name")
    room = ChatRoom.query.filter_by(name=room_name).first()
    if room:
        join_request = JoinRequest(user_id=current_user.id, room_id=room.id)
        db.session.add(join_request)
        db.session.commit()
        return render_template('chat.html', message="Join request sent to admin.")
    else:
        return render_template('chat.html', message="Error: room doesn't exist")
    
@app.route("/approve_join/<int:request_id>", methods=["POST"])
@login_required
def approve_join(request_id):
    join_request = JoinRequest.query.get(request_id)
    if not join_request:
        return render_template('chat.html', message="Error: join request not found")
    
    room = ChatRoom.query.get(join_request.room_id)
    if room.admin_id != current_user.id:
        return render_template('chat.html', message="Error: you are not the admin of this room")
    
    # Approve the join request
    user = User.query.get(join_request.user_id)  # Retrieve the requesting user
    user.rooms.append(room)  # Add the requesting user to the room
    db.session.delete(join_request)
    db.session.commit()

    return render_template('chat.html', message="User has been added to the room successfully")
@app.route("/view_requests")
@login_required
def view_requests():
    join_requests = JoinRequest.query.join(ChatRoom, ChatRoom.id == JoinRequest.room_id)\
                                     .filter(ChatRoom.admin_id == current_user.id).all()
    return render_template('request.html', join_requests=join_requests)

@app.route("/public_key/<string:room_id>", methods=["GET"])
@login_required
def get_public_keys(room_id):
    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    return jsonify({'public_key': room.rsa_public_key})

@app.route("/private_key/<string:room_id>", methods=["GET"])
@login_required
def get_private_keys(room_id):
    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    return jsonify({'private_key': room.rsa_private_key})


@app.route("/join_chat_room", methods=["POST"])
@login_required
def join_chat_room():
    room_name = request.form.get("room_name")
    room = ChatRoom.query.filter_by(name=room_name).first()
    if room:
        current_user.rooms.append(room)  # Associate the current user with the room
        db.session.commit()
        return render_template('chat.html', message="Room joined successfully")
    else:
        return render_template('chat.html', message="Error: room doesn't exist")

# Search chatroom
@app.route("/live_search_chatroom", methods=["POST"])
@login_required  
def live_search_chatroom():
    search_query = request.form.get("search_query")

    if not search_query:
        return ""

    # Perform a database query to find chatrooms matching the search query
    matching_rooms = ChatRoom.query.filter(
        ChatRoom.name.ilike(f"%{search_query}%"),
        ChatRoom.users.any(id=current_user.id)
    ).all()

    # Create an HTML response with list items for the search results
    response_html = ""
    for room in matching_rooms:
        response_html += f'<li><a href="{url_for("chat_room", room_id=room.id)}">{room.name}</a></li>'

    return response_html

#404 error handling
@app.errorhandler(404) 
def not_found(e): 
  
  return render_template("404.html") 

@app.route("/chat_room/<string:room_id>", methods=["GET"])
@login_required
def chat_room(room_id):
    room = ChatRoom.query.get(room_id)

    # Check if the current user is a member of the chat room
    if current_user in room.users:
        # The user has permission to access the room
        rooms = current_user.rooms
        previous_messages = ChatMessage.query.filter_by(room=room).all()
        return render_template("chat_window.html", room=room, previous_messages=previous_messages, rooms=rooms)
    else:
        # User is not a member of the room, return a 403 Forbidden status
        return render_template("403.html")


#get all the active users
@app.route("/active_users/<string:room_id>", methods=["GET"])
@login_required
def get_active_users(room_id):
    room = ChatRoom.query.get(room_id)
    active_users = room.users
    
    return jsonify([{"id": user.id, "username": user.username} for user in active_users])

#settings page
@app.route("/settings",methods=['GET'])
@login_required
def settng_page():
    #print(current_user.username)
    return render_template('settings.html')

#change avatar page
@app.route("/change_avatar", methods=["POST"])
@login_required
def change_avatar():
    if 'avatar' in request.files:
        avatar = request.files['avatar']
        if avatar.filename != '':
            # Save the uploaded avatar to the server's file system
            ext = avatar.filename.split(".")[-1]
            avatar_filename = f'avatar_{current_user.username}'
            avatar_filename+=(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6)))
            avatar_filename += f'.{ext}'
            avatar_path = os.path.join(app.config['AVATARS_FOLDER'], avatar_filename)
            avatar.save(avatar_path)

            # Update the user's profile_pic to the new avatar path
            current_user.profile_pic = url_for('upload_avatar', filename=avatar_filename)
            db.session.commit()

    return redirect(url_for('settng_page'))

@app.route("/video_room", methods=["GET", "POST"])
def video_room():
    if request.method == "POST":
        room_id = request.form['room_id']
        return redirect(url_for("entry_checkpoint", room_id=room_id))

    return render_template("video_room.html")

@app.route("/room/<string:room_id>/")
def enter_room(room_id):
    if room_id not in session:
        return redirect(url_for("entry_checkpoint", room_id=room_id))
    return render_template("chatroom.html", room_id=room_id, display_name=session[room_id]["name"], mute_audio=session[room_id]["mute_audio"], mute_video=session[room_id]["mute_video"])

@app.route("/room/<string:room_id>/checkpoint/", methods=["GET", "POST"])
def entry_checkpoint(room_id):
    if request.method == "POST":
        display_name = request.form['display_name']
        mute_audio = request.form['mute_audio']
        mute_video = request.form['mute_video']
        session[room_id] = {"name": display_name, "mute_audio":mute_audio, "mute_video":mute_video}
        return redirect(url_for("enter_room", room_id=room_id))

    return render_template("chatroom_checkpoint.html", room_id=room_id)


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# SocketIO stuff
@socketio.on('join_room')
def handle_join_room_event(data):
    room = data['room']
    join_room(room)
    socketio.emit('join_room_announcement', data, room=data['room'])

@socketio.on('leave_room')
def handle_leave_room_event(data):
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])

@socketio.on('send_message')
def handle_message(data):
    room_id = data['room_id']
    encrypted_keys = data['encrypted_keys']
    encrypted_content = data['encrypted_content']
    user_id = current_user.id
    username = current_user.username
    profile_pic = current_user.profile_pic
    def import_private_key(pem):
        pem_lines = pem.strip().split('\n')
        pem_data = ''.join(pem_lines[1:-1])
        import base64
        binary_der = base64.b64decode(pem_data)
        private_key = RSA.import_key(binary_der)
        return private_key
    private_key= import_private_key(ChatRoom.query.get(room_id).rsa_private_key)
    print(private_key)
    print(bytes(encrypted_keys['encryptedAesKey'],'utf-8'))
    cipher = PKCS1_OAEP.new(private_key)
    
    # print(encrypted_content)
    # print(encrypted_keys)
    
    # Save the message to the database
    message = ChatMessage(id=create_id(),content=data['m'], room_id=room_id, user_id=user_id)
    db.session.add(message)
    db.session.commit()

    # Emit the message to all clients in the room, including the sender
    data = {'profile_pic':profile_pic,'user_id':user_id,'username': username, 'content': encrypted_content, 'message_id': message.id,'keys':encrypted_keys}
    socketio.emit('receive_message', data, room=room_id)

@socketio.on('send_file')
def handle_file(data):
 
    
    room_id = data['room_id']
    file_contents = data['file_contents']
    file_extensions = data['file_extensions']
    user_id = current_user.id
    profile_pic = current_user.profile_pic
    
    for file_content, file_extension in zip(file_contents, file_extensions):
        if len(file_content) > (32 * 1024 * 1024):
            emit('file_error', {'message': 'File size should be less than 32 MB.'})
            continue


        # Save the file to the server's file system
        name = f"{datetime.now().timestamp()}".replace(".","_")
        file_name = f"{name}.{file_extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Create a file message in the database
        message = ChatMessage(
            id = create_id(),
            content="File: " + file_name,
            room_id=room_id,
            user_id=user_id,
            file_path=file_path,
            file_name=file_name
        )

        db.session.add(message)
        db.session.commit()

        # Emit the file message to all clients in the room, including the sender
        data = {'profile_pic':profile_pic,'user_id':user_id,'username': current_user.username, 'content': "File: " + file_name, 'file_path': url_for('uploaded_file', filename=file_name),'message_id': message.id}
        socketio.emit('receive_message', data, room=room_id)




@socketio.on('send_voice_message')
def send_voice(data):
    print("[*]Received..")
    room_id = data['room_id']
    voice_data = data['voice_data']
    user_id = current_user.id
    profile_pic = current_user.profile_pic

    name = f"{datetime.now().timestamp()}".replace(".","_")
    file_name = f"{name}.wav"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

    with open(file_path,'wb') as f:
        f.write(voice_data)

    message = ChatMessage(
        id = create_id(),
        content="File: " + file_name,
        room_id=room_id,
        user_id=user_id,
        file_path=file_path,
        file_name=file_name
    )

    db.session.add(message)
    db.session.commit()

    data = {'profile_pic':profile_pic,'user_id':user_id,'username': current_user.username, 'content': "File: " + file_name, 'file_path': url_for('uploaded_file', filename=file_name),'message_id': message.id}
    socketio.emit(
        'receive_voice_message',data,room=room_id
    )

@socketio.on('delete_message')
def handle_delete_message(data):
    message_id = data.get('message_id')
    room_id = data.get('room_id')
    # print(message_id)
    # print(room_id)

    # Check if the current user has permission to delete the message
    message = ChatMessage.query.get(message_id)
    if message and message.user_id == current_user.id and message.room_id == room_id:
        # Delete the message from the database
        db.session.delete(message)
        db.session.commit()

        # Emit an event to inform all clients in the room to delete the message
        socketio.emit('message_deleted', {'message_id': message_id, 'room_id': room_id}, room=room_id)

# web rtc stuff
@socketio.on("connect")
def on_connect():
    sid = request.sid
    print("New socket connected ", sid)
    

@socketio.on("join-room")
def on_join_room(data):
    sid = request.sid
    room_id = data["room_id"]
    display_name = session[room_id]["name"]
    
    # register sid to the room
    join_room(room_id)
    _room_of_sid[sid] = room_id
    _name_of_sid[sid] = display_name
    
    # broadcast to others in the room
    print("[{}] New member joined: {}<{}>".format(room_id, display_name, sid))
    emit("user-connect", {"sid": sid, "name": display_name}, broadcast=True, include_self=False, room=room_id)
    
    # add to user list maintained on server
    if room_id not in _users_in_room:
        _users_in_room[room_id] = [sid]
        emit("user-list", {"my_id": sid}) # send own id only
    else:
        usrlist = {u_id:_name_of_sid[u_id] for u_id in _users_in_room[room_id]}
        emit("user-list", {"list": usrlist, "my_id": sid}) # send list of existing users to the new member
        _users_in_room[room_id].append(sid) # add new member to user list maintained on server

    print("\nusers: ", _users_in_room, "\n")


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    room_id = _room_of_sid[sid]
    display_name = _name_of_sid[sid]

    print("[{}] Member left: {}<{}>".format(room_id, display_name, sid))
    emit("user-disconnect", {"sid": sid}, broadcast=True, include_self=False, room=room_id)

    _users_in_room[room_id].remove(sid)
    if len(_users_in_room[room_id]) == 0:
        _users_in_room.pop(room_id)

    _room_of_sid.pop(sid)
    _name_of_sid.pop(sid)

    print("\nusers: ", _users_in_room, "\n")


@socketio.on("data")
def on_data(data):
    sender_sid = data['sender_id']
    target_sid = data['target_id']
    if sender_sid != request.sid:
        print("[Not supposed to happen!] request.sid and sender_id don't match!!!")

    if data["type"] != "new-ice-candidate":
        print('{} message from {} to {}'.format(data["type"], sender_sid, target_sid))
    socketio.emit('data', data, room=target_sid)

if __name__ == '__main__':
    create_db()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
