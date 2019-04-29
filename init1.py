#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    username = request.form['username']
    password = request.form['password']
    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    data = cursor.fetchone()
    cursor.close()
    error = None
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    username = request.form['username']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']
    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (username, password, fname, lname))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    username = session['username']
    cursor = conn.cursor();
    query = '''SELECT timestamp, caption, photoOwner, filePath, photoID FROM Photo
               WHERE photoOwner = %s
               OR allFollowers = %s 
               OR Photo.photoID IN (SELECT photoID FROM Share, Belong 
                               WHERE Share.groupName = Belong.groupName && Belong.username = %s)
               ORDER BY timestamp DESC'''
    cursor.execute(query, (username, 1, username))
    data = cursor.fetchall()

    groupQuery = '''SELECT DISTINCT groupName FROM CloseFriendGroup NATURAL JOIN Belong WHERE username = %s'''
    cursor.execute(groupQuery, (username))
    groupData = cursor.fetchall()

    getComments = 'SELECT commentText, photoID, timestamp, username FROM Comment'
    cursor.execute(getComments)
    commentLists = cursor.fetchall()

    getTag = 'SELECT * FROM Tag WHERE username = %s AND acceptedTag = 0'
    cursor.execute(getTag, (username))
    pending_tags = cursor.fetchall()

    taggableQuery = '''SELECT username FROM Person'''
    cursor.execute(taggableQuery)
    taggableData = cursor.fetchall()

    taggedQuery = '''SELECT * FROM Tag NATURAL JOIN Person'''
    cursor.execute(taggedQuery)
    taggedData = cursor.fetchall()

    getFollow = 'SELECT * FROM Follow WHERE followeeUsername = %s AND acceptedFollow = 0'
    cursor.execute(getFollow, (username))
    pendingFollows = cursor.fetchall()

    cursor.close()
    return render_template('home.html', username=username, posts=data, groups=groupData, commentlist=commentLists, pending_tags = pending_tags, taggable = taggableData, tagged = taggedData, pendingFollows = pendingFollows)

        
@app.route('/post', methods=['GET', 'POST'])
def post():
    photoOwner = session['username']
    cursor = conn.cursor();
    caption = request.form['caption']
    filePath = request.form['filePath']
    allFollowers = request.form['allFollowers']

    #case 1: photo is open to all followers
    if allFollowers:
        query = '''INSERT INTO Photo (caption, photoOwner, filePath, allFollowers) 
                   VALUES(%s, %s, %s, %s)'''
        cursor.execute(query, (caption, photoOwner, filePath, allFollowers))
    #case 2: photo only visible to closeFriendsGroup
    else:
        q = 'SELECT groupName FROM closeFriendGroup WHERE groupName = %s'
        cursor.execute(q,(group))
        selectFriendGroup = cursor.fetchone()
        if (selectFriendGroup):
            queryToFindfgOwner = 'SELECT groupOwner FROM Belong WHERE groupName = %s and groupOwner = %s'
            cursor.execute(queryToFindfgOwner, (group, username))
            owner = cursor.fetchone()
            if(owner):
                owner = owner.get('groupOwner')
            if(not owner):
                flash("Friend group does not exist")
                return redirect(url_for('home'))
            queryToPost = 'INSERT INTO Photo(caption, photoOwner, filePath, allFollowers) VALUES(%s, %s, %s, %s)'
            cursor.execute(queryToPost, (Content, username, file_path, 0))
            content_id = cursor.lastrowid #returns the value generated for an AUTO_INCREMENT column by the previous INSERT
            queryToShare = 'INSERT INTO Share (photoID, groupName, groupOwner) VALUES (%s, %s, %s)'
            cursor.execute(queryToShare, (content_id, group, username))

    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/select_blogger')
def select_blogger():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT photoOwner FROM Photo'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = '''SELECT timestamp, caption FROM Photo 
               WHERE photoOwner = %s ORDER BY timestamp DESC'''
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)


#NEW DEFINITIONS
#ADD FRIEND
#ADDFRIENDAUTH
#CREATE (creates closefriendsgroups)
#MANAGE (manage tag requests)
#TAG (tags a user to a photo)

@app.route('/addFriendAuth', methods=['GET', 'POST'])
def addFriendAuth():
    username = session['username']
    person = request.form['person']
    cursor = conn.cursor();
    query = 'SELECT * FROM Follow WHERE followeeUsername = %s AND followerUsername = %s'
    cursor.execute(query,(person, username))
    data = cursor.fetchone()

    if (username == person):
        flash("Cannot follow self.")
        return redirect(url_for('home'))

    if(data): #if pairing exists
        existing_friend = 'SELECT * FROM Follow WHERE followerUsername = %s and followeeUsername = %s and acceptedFollow = 1'
        cursor.execute(existing_friend, (username, person))
        existing_friend_data = cursor.fetchone()
        if(existing_friend_data): #if pairing exists but hasnt accepted request yet
            flash("Already friends.")
            return redirect(url_for('home'))
        else: #if pairing 
            flash("Alredy sent friend request.")
            return redirect(url_for('home'))
    else: #pairing dne
        flash("Friend request sent!")
        ins = 'INSERT INTO Follow(followerUsername, followeeUsername, acceptedFollow) VALUES(%s, %s, 0)'
        cursor.execute(ins, (username, person))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))


@app.route('/addFriendToGroupAuth', methods=['GET', 'POST'])
def addFriendToGroupAuth():
    username = session['username']
    closeFriendGroup = request.form['closeFriendGroup']
    fUsername = request.form['fUsername']
    cursor = conn.cursor();
    query = 'SELECT groupName, groupOwner FROM CloseFriendGroup WHERE groupName = %s AND groupOwner = %s'
    cursor.execute(query,(closeFriendGroup, username))
    data = cursor.fetchone()
    if(data):
        check_friend = 'SELECT username FROM Person WHERE username = %s'
        cursor.execute(check_friend, fUsername)
        fdata = cursor.fetchone()
        if(fdata):
            existing_friend = 'SELECT username FROM Belong WHERE username = %s and groupName = %s and groupOwner = %s'
            cursor.execute(existing_friend, (fUsername, closeFriendGroup, username))
            existing_friend_data = cursor.fetchone()
            if(not existing_friend_data):
                ins = 'INSERT INTO Belong VALUES(%s, %s, %s)'
                cursor.execute(ins, (fUsername, closeFriendGroup, username))
                conn.commit()
                cursor.close()
                return redirect(url_for('home'))
            else:
                flash("Username already in friend group")
                return redirect(url_for('home'))
        else:
            flash("Username does not exist")
            return redirect(url_for('home'))
    else:
        flash("Friend group does not exist")
        return redirect(url_for('home'))

@app.route('/create', methods=['GET', 'POST'])
def createFG():
    username = session['username']
    friend = request.form['friend']
    group_name = request.form['group_name']
    cursor = conn.cursor()
    query = 'SELECT groupOwner FROM CloseFriendGroup WHERE groupName = %s and groupOwner = %s'
    cursor.execute(query, (group_name, username))
    checkGroupName = cursor.fetchone()
    if(checkGroupName):
        flash("Group already exists")
        return redirect(url_for('home'))

    checkFriend = 'SELECT username FROM Person WHERE username = %s'
    cursor.execute(checkFriend, (friend))
    fUsername = cursor.fetchone()
    if(not fUsername):
        flash("Username does not exist")
        return redirect(url_for('home'))
    if(friend == username):
        flash("You cannot add yourself!")
        return redirect(url_for('home'))
            
    else:               
        ins= 'INSERT INTO CloseFriendGroup(groupName, groupOwner) VALUES(%s, %s)'
        cursor.execute(ins, (username, group_name));
        ins_member= 'INSERT INTO Belong(groupName, groupOwner, username) VALUES(%s, %s, %s)'
        cursor.execute(ins_member, (group_name, username, friend));
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/manageTags', methods=['GET', 'POST'])
def managetags():
    username = session['username']
    answer = request.form['answer'] #
    photoID = request.form['id']
    cursor = conn.cursor()
    if(answer == '1'):
        query = 'UPDATE Tag SET acceptedTag = 1 WHERE username = %s AND photoID = %s'
        cursor.execute(query, (username, photoID))
    else:
        query = 'DELETE FROM Tag where  username = %s AND photoID = %s '
        cursor.execute(query, (username, photoID))
    conn.commit()

    cursor.close()
    return redirect(url_for('home'))


@app.route('/manageFollows', methods=['GET', 'POST'])
def managefollows():
    username = session['username']
    answer = request.form['answer'] #
    follower = request.form['followerUsername']
    cursor = conn.cursor()
    if(answer == '1'): #if accepted request
        query = 'UPDATE Follow SET acceptedFollow = 1 WHERE followeeUsername = %s AND followerUsername = %s'
        cursor.execute(query, (username, follower))
    else:
        query = 'DELETE FROM Follow where  followeeUsername = %s AND followerUsername = %s '
        cursor.execute(query, (username, follower))
    conn.commit()

    cursor.close()
    return redirect(url_for('home'))


@app.route('/tag', methods=['GET', 'POST'])
def tag():
    username = session['username']
    cursor = conn.cursor();
    photoID = request.form['photoID']
    taggee = request.form['taggee']
    status = 0
    
    #checking if same tag already exists
    queryToCheckTag = 'SELECT * FROM Tag WHERE photoID = %s AND username = %s'
    cursor.execute(queryToCheckTag,(photoID, taggee))
    tagExists = cursor.fetchone()

    if (tagExists):
        flash("Tag already exists")
        return redirect(url_for('home'))
                
    validUser = 'SELECT username FROM Person WHERE username = %s'
    cursor.execute(validUser,(taggee))
    userExists = cursor.fetchone()
    if(not userExists):
        flash("Cannot add tag: User does not exist.")
        return redirect(url_for('home'))

    #tagging
    status = 0
    queryToPostTag = 'INSERT INTO Tag(photoID, username, acceptedTag) VALUES (%s, %s, %s)'
    cursor.execute(queryToPostTag,(photoID, taggee, status))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
