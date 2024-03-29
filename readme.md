<center>
  <h1>LinkUp</h1>
</center>

# Table of Contents
- [Description](#Description)
- [Demo](#Demo)  
- [Installations](#Installation)
- [Features](#Features)
- [Todo & Future Scope](#Todo--Future-Scope)
- [Contributors](#Contributors)


# Description
"LinkUp: Empowering seamless connections. A Flask-SocketIO chat application with chatroom creation, persistent chat history, voice messaging, file sharing, and profile picture features for a dynamic and engaging communication experience."

# Demo

### Authentication

https://github.com/alpha-hexor/LinkUp/assets/83006189/ea32ce2e-f799-4da9-b7a9-ab6b362879f9

### Chatroom Management

https://github.com/alpha-hexor/LinkUp/assets/83006189/275f82a9-90df-41df-8389-1e6abe50d055

### Chat and Media Sharing

https://github.com/alpha-hexor/LinkUp/assets/83006189/2ffedf40-9eb7-4d13-85d4-8fe26756e7e8

### Profile Pic Change

https://github.com/alpha-hexor/LinkUp/assets/83006189/5059a835-8230-43bb-adea-0f2f5415239c


# Installation

To run the appplication locally do the following

* Clone the repo
```sh
git clone https://github.com/alpha-hexor/LinkUp.git
```

* Change directory
```sh
cd LinkUp
```

* Create database
```sh
touch mydatabase.db # change as per in the code
```

* Install Requirements
```sh
pip install -r requirements.txt
```

* Launch
```sh
python app.py
```
**The interface should be availabel on http://127.0.0.1:5000/**


# Features
**Our chat application has the following features :-** 

### Authentication

*We have authentication system so that a new user can create an account and log in. We store the passwords in bcrypt hash format for security. Proper error message is shown for faulty authentication attempts.*


### Chatroom management

*When logged in the user can create a new chatroom and share the names with another user or the user can join an already created chatroom.*


### Chatroom Search

*A chatroom search feature is provide so that users can search their already joined chatroom and can continue the chat.*


### Synchronized Chat

*We implemented synchronized chatting with the help of socketio so that sent message can be seen by all the logged in users.* 


### Chat History

*All the chats are being saved in the database constantly so if a new user logs in the chatroom or an extising user loggs in again they can easily see the previous messages.*


### Delete Chat

*Users can delete their recently sent text message. But they can't delete chat if it's long time ago.*  


### File Sharing

*We implemented file sharing so that users can share files with each other. Users can send files maximum size of 32 mb and also they can send 8 files in a row.* 


### Audio Message

*Users can send audio messages for better communication.*


### Setting Profile Pic
*Users can change profile pics to their liking for a better social media like experience.*

## Todo && Future Scope

- **We can implement webrtc so that we can use this for video and audio call**

- **We can add friend request feature so that only two user can chat personally**

- **Make the whole website more responsive for mobile users**

- **Right now the codebase is not production ready so we have to make the changes to make it production ready**

- **Clean up the codebase for better understandings and future improvements**

# Contributors

| Contributor   | Responsibility     |
| ------------- | ------------------- |
| Piyush Ghughu      | Frontend Design |
| Rajdeep Choudhury    | Chatroom Management       |
| Sneha Chakraborty  | Authentication and Database Design             |
| Souvik Das | Full chat managent |
| Niladri Dhar | Multimedia Sharing and Documentation |









