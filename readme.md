<center>
  <h1>LinkUp</h1>
</center>

# Table of Contents
- [Description](#Description)
- [Installations](#Installation)
- [Features](#Features)
- [Todo & Future Scope](#Todo--Future-Scope)
- [Contributors](#Contributors)


# Description
"LinkUp: Empowering seamless connections. A Flask-SocketIO chat application with chatroom creation, persistent chat history, voice messaging, file sharing, and profile picture features for a dynamic and engaging communication experience."

# Installation

To run the appplication locally do the following

* Run the following

``sh
docker compose up
``

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









