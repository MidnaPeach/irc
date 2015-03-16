#server.py
#test

import psycopg2
import psycopg2.extras
import traceback

import os
import uuid
from flask import Flask, session
from flask.ext.socketio import SocketIO, emit

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app)

def connectToDB():
  #print 'in connectToDB'
  connectionString = 'dbname=irc_db user=postgres password=pg host=localhost'
  try:
    return psycopg2.connect(connectionString)
  except:
    print("Can't connect to database - in server.py")
    traceback.print_exc()

messages = [{'text':'test', 'name':'testName'}]


#USERS IS A DICTIONARY
users = {} 


#WHat the actual is this thing doing.
def updateRoster():
    print 'IN UPDATEROSTER'
    names = []
    for user_id in  users:
        print users[user_id]['username']
        if len(users[user_id]['username'])==0:
            names.append('Anonymous')
        else:
            names.append(users[user_id]['username'])
    print 'broadcasting names'
    traceback.print_exc()
    emit('roster', names, broadcast=True)

#CONNECT    
@socketio.on('connect', namespace='/chat') #handles the connect event
def test_connect():
    print 'IN CONNECT'
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    session['uuid']=uuid.uuid1()# each time a uuid is called,
                                # a new number is returned

    session['username']='starter name'
    #print 'connected'
    
    #this means that it goes to the users list thing and gets the session id 
    #this instance of the chat and makes the username field = new user
    
    users[session['uuid']]={'username':'New User'}
    
    updateRoster()
    
    for item in messages:
        emit('message', item)

#MESSAGE
#THIS IS ON LINE 55 IN INDEX.HTML $scope.send - emits message and text
@socketio.on('message', namespace='/chat')
def new_message(message):
    print 'IN MESSAGE'
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    #testing statements
    #print 'the message typed was:' + message
    
    messageToGoInDB = message
    
    #get id here from users
    posterIdQuery = "SELECT id FROM users;"
    try:
        cur.execute(posterIdQuery)
    except:
        print("couldn't get posterID from users!")
    listOfPosterIDs = cur.fetchall()
    
    originalPosterID = -7
    #testing statements
    #for userId in listOfPosterIDs:
    #    print 'the user id is:' + str(userId)
            
    #set originalPosterId to correct ID
    #first get the username of the person who is posting.
    thisSessionNum = session['uuid']
    currentUsername = users[thisSessionNum]['username']
   
    #then go through database and get that user's id
    userIdSelectQuery = "SELECT id FROM users WHERE username = %s"
    try:
        cur.execute(userIdSelectQuery, (currentUsername,))
    except:
        print("I had a problem getting the users id from their username.")
    usersIdResult = cur.fetchone()
    
    originalPosterID = usersIdResult[0] 
    
    #insert message into the database    
    insertStatement = "INSERT INTO messages (original_poster_id, message_content) VALUES (%s, %s)"
    try: 
        cur.execute(insertStatement, (originalPosterID, messageToGoInDB));
    except:
        print "there was an error with the insert"
        traceback.print_exc()
        
    conn.commit()
    
    #take what is in the database, take from the users column and then make it into a python dict called users
    tmp = {'text':message, 'username':session['username']}
    #user is not a real thing yet, its also just an iterator in python. 
    #users is supposed to be the results from the database.
    
    thisSessionNum = session['uuid']
    user = users[thisSessionNum]['username']
    #print 'user is :' + user
    if user in users:
        tmp = {'text':message, 'username':user}
    
    #messages is a list of python dictionaries that look like {messages,users} 
    messages.append(tmp)
    
    print("we are passing this stuff as tmp")
    
    #print messages here and find out what is being passed in
    
    emit('message', tmp, broadcast=True)

#IDENTIFY    
#LINE 76ish in index.html? $scope.setName - emits identify scope.name
# $scope.setName2 also emits identify, $scope.name2
@socketio.on('identify', namespace='/chat')
def on_identify(userTypedLoginInfo):
    print 'IN IDENTIFY'
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    #print 'identify' + userTypedLoginInfo
    #the message here is where we need to connect to check against the database??
    
    #userTypedLogininfo is the real time variable that is displaying in the server console window and it is being displayed as 
    #the user types things into the username box.
    #we might need to get the username from here and the password from here and get the thing
    users[session['uuid']]={'username':userTypedLoginInfo}
    updateRoster()
    
#LOGIN
#around line 85 index.html $scope.processLogin - emits login, $scope.password
@socketio.on('login', namespace='/chat')
def on_login(loginInfo):
    print 'IN LOGIN'
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    usernameVar = loginInfo['username']
    passwordVar = loginInfo['password']
    #THIS DOESN"T WORK YET
    #print 'user:' + loginInfo['username']
    #print 'pass:'  + loginInfo['password']
    
    user_select_string = "SELECT username FROM users WHERE username = %s AND password = %s;"

    try:
        cur.execute(user_select_string,(usernameVar, passwordVar));
        #print 'executed query'
        currentUser = cur.fetchone()

        if(currentUser is None):
            print 'this is not a valid login, please try again'
        else:
            
            #print 'successfully fetched one value'
        
            #print 'sessionuser:' + session['username']
            #print 'sessionpass:' + session['password']        
        
            #print 'currentUser:' + str(currentUser)
            #print 'sessionpass:' + session['password']        
        
            session['username'] = currentUser['username']
            #session['password'] = currentUser['password']

            print 'Logged on as:' + session['username'] 
    except:
        print 'could not execute login query!'
        traceback.print_exc()
    
    #printing all previous messages from database here.
    #now get stuff from database and display that
    messageQuery = "select message_content, original_poster_id from messages;"
    
    try:
        cur.execute(messageQuery)
    except:
        print("I couldn't grab messages from the previous database")
    
    previousMessages = cur.fetchall()
    oldMessages = {}
    #oldMessagesInitialize = {'text':'oldMessageInitText', 'username':'oldMessageInitUsername'} 
        
    for message in previousMessages:
        messagestr = str(message['message_content'])
        print 'a previous message was:' + messagestr
        idStr = str(message['original_poster_id'])
        #print 'the users id was: ' + idStr
        
        #now get the id and match it with the username that it goes to
        
    #get posterId from messages
    messagesPosterIdQuery = "SELECT original_poster_id FROM messages;"
    try:
        cur.execute(messagesPosterIdQuery)
    except:
        print("couldn't get posterID from messages!")
    
    listOfPosterIDsFromMessages = cur.fetchall()

    for messagesUserId in listOfPosterIDsFromMessages:
        userIdStringFromInt = str(messagesUserId[0])
        #print 'the user id is:' + userIdStringFromInt
    
        #oldMessages['username'] = 
    
    
    
    #what why is this commented out. zacharski did that and I don't know. 
    #users[session['uuid']]={'username':message}
    #updateRoster()
    
#DISCONNECT
@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    print 'DISCONNECT'
    #disconnect happens when you close the thing!
    if session['uuid'] in users:
        del users[session['uuid']]
        updateRoster()

@socketio.on('search')
def on_search(searchValue):
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    print 'SEARCH'
    search_select = "SELECT * FROM messages WHERE content LIKE %%s%;"
    cur.execute(search_select, (searchValue,))


@app.route('/')
def hello_world():
    print 'in hello world'
    return app.send_static_file('index.html')
    return 'Hello World!'

@app.route('/js/<path:path>')
def static_proxy_js(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('js', path))
    
@app.route('/css/<path:path>')
def static_proxy_css(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('css', path))
    
@app.route('/img/<path:path>')
def static_proxy_img(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('img', path))
    
if __name__ == '__main__':
    print "A"

    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
    print 'B'
