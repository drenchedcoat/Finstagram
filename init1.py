#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
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
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    ##query = 'SELECT * FROM user WHERE username = %s and password = %s'
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    ##query = 'SELECT * FROM user WHERE username = %s'
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ##ins = 'INSERT INTO user VALUES(%s, %s)'
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (username, password, fname, lname))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    username = session['username']
    cursor = conn.cursor();
    ##query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    query = '''SELECT timestamp, caption, photoOwner, filePath FROM Photo
               WHERE photoOwner = %s
               ORDER BY timestamp DESC'''
    cursor.execute(query, (username))
    data = cursor.fetchall()

    groupQuery = '''SELECT DISTINCT groupName FROM CloseFriendGroup NATURAL JOIN Belong WHERE username = %s'''
    cursor.execute(groupQuery, (username))

    cursor.close()
    return render_template('home.html', username=username, posts=data, groups=groupQuery)

        
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
    #case 2: photo only visible to cloeFriendsGroup
    else:
        q = 'SELECT groupName FROM closeFriendGroup WHERE groupName = %s'
        cursor.execute(q,(group))
        selectFriendGroup = cursor.fetchone()
        if (selectFriendGroup):
        #for group in selectFriendGroup:
                queryToFindfgOwner = 'SELECT username_creator FROM member WHERE group_name = %s and username_creator = %s'
                cursor.execute(queryToFindfgOwner, (group, username))
                owner = cursor.fetchone()
                if(owner):
                        owner = owner.get('username_creator')
                if(not owner):
                          #error = "Friend group does not exist"
                          #return render_template('home.html', username=username, perror=error)
                          flash("Friend group does not exist")
                          return redirect(url_for('home'))
                queryToPost = 'INSERT INTO Content(content_name, username, file_path, public) VALUES(%s, %s, %s, %s)'
                cursor.execute(queryToPost, (Content, username, file_path,0))
                content_id = cursor.lastrowid #returns the value generated for an AUTO_INCREMENT column by the previous INSERT
                queryToShare = 'INSERT INTO Share (id, group_name, username) VALUES (%s, %s, %s)'
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
