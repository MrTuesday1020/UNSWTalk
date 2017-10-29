# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os
import re
import sqlite3
from flask import Flask, render_template, session, request, redirect, url_for
from shutil import copyfile
from time import gmtime, strftime, time
import subprocess
from werkzeug.utils import secure_filename

############################# connect database #############################
# dataset
students_dir = "dataset-medium";
cx = sqlite3.connect('./UNSWtalk.db', check_same_thread = False)
#cx = sqlite3.connect(":memory:", check_same_thread = False)
cu = cx.cursor()

############################# database functions #############################
def findStudentByZid(zid):
    find_student_statement = "select * from students where zid =  '" + zid + "';"
    cu.execute(find_student_statement)
    result = cu.fetchall()
    if len(result) == 0:
        return 1
    elif len(result) > 1:
        return 2
    else:
        student = {}
        student["id"] = result[0][0]
        student["zid"] = result[0][1]
        student["password"] = result[0][2]
        student["photo"] = result[0][3]
        student["full_name"] = result[0][4]
        student["program"] = result[0][5]
        student["courses"] = result[0][6]
        student["email"] = result[0][7]
        student["birthday"] = result[0][8]
        student["home_longitude"] = result[0][9]
        student["home_latitude"] = result[0][10]
        student["home_suburb"] = result[0][11]
        student["profile"] = result[0][12]
        student["background"] = result[0][13]
        student["status"] = result[0][14]
        return student


def findStudentByEmail(email):
    find_student_statement = "select * from students where email =  '" + email + "';"
    cu.execute(find_student_statement)
    result = cu.fetchall()
    if len(result) == 0:
        return 1
    elif len(result) > 1:
        return 2
    else:
        student = {}
        student["id"] = result[0][0]
        student["zid"] = result[0][1]
        student["password"] = result[0][2]
        student["photo"] = result[0][3]
        student["full_name"] = result[0][4]
        student["program"] = result[0][5]
        student["courses"] = result[0][6]
        student["email"] = result[0][7]
        student["birthday"] = result[0][8]
        student["home_longitude"] = result[0][9]
        student["home_latitude"] = result[0][10]
        student["home_suburb"] = result[0][11]
        student["profile"] = result[0][12]
        student["background"] = result[0][13]
        student["status"] = result[0][14]
        return student


def findFriendsByZid(zid):
    friends = []
    find_freinds_statement = "select friends.zid2, students.photo, students.full_name, students.status from friends, students where friends.zid1 = \"" + zid + "\" and friends.zid2 = students.zid union select friends.zid1, students.photo, students.full_name, students.status from friends, students where friends.zid2 = \"" + zid + "\" and friends.zid1 = students.zid;"
    cu.execute(find_freinds_statement)
    results = cu.fetchall()
    for result in results:
        if result[3] != 1:
            continue
        friends.append({"zid":result[0], "photo":result[1], "full_name":result[2]})
    return friends

def findPostsByZid(zid):
    friends = findFriendsByZid(zid)
    zids = ""
    for friend in friends:
        zids += "'" + friend["zid"] + "', "
    zids += "'" + zid + "'"
    find_posts_statement = "select students.zid, students.photo, students.full_name, posts.postseq, posts.message, posts.time, posts.latitude, posts.longitude, students.status from posts, students where posts.zid = students.zid and posts.zid in (" + zids + ") order by posts.time desc;"
    cu.execute(find_posts_statement)
    results = cu.fetchall()
    posts = []
    for result in results:
        if result[8] != 1:
            continue 
        post = {}
        post["zid"] = result[0]
        post["photo"] = result[1]
        post["full_name"] = result[2]
        post["postseq"] = result[3]
        #message = re.sub(r"\\n", "<br>", result[4]
        message = re.sub(r"\"\"", "\"", result[4])
        post["message"] = message
        post["time"] = result[5]
        post["latitude"] = result[6]
        post["longitude"] = result[7]
        posts.append(post)
    return posts

def findPostsByPostSeq(postseq):
    find_post_statement = "select students.zid, students.photo, students.full_name, posts.id, posts.postseq, posts.message, posts.time, posts.latitude, posts.longitude from posts, students where posts.zid = students.zid and posts.postseq = '" + postseq + "';"
    cu.execute(find_post_statement)
    result = cu.fetchone()
    post = {}
    post["zid"] = result[0]
    post["photo"] = result[1]
    post["full_name"] = result[2]
    post["id"] = result[3]
    post["postseq"] = result[4]
    #message = re.sub(r"\\n", "<br>", result[5]
    message = re.sub(r"\"\"", "\"", result[5])
    post["message"] = message
    post["time"] = result[6]
    post["latitude"] = result[7]
    post["longitude"] = result[8]
    return post

def findCommentsByPostSeq(postseq):
    find_comments_statement = "select comments.*, students.photo, students.full_name, students.status from comments,students where comments.zid = students.zid and comments.postseq = '" + postseq + "' order by comments.time desc;"
    cu.execute(find_comments_statement)
    results = cu.fetchall()
    comments=[]
    for result in results:
        if result[10] != 1:
            continue
        comment={}
        comment["id"] = result[0]
        comment["commentseq"] = result[1]
        comment["postseq"] = result[2]
        comment["zid"] = result[3]
        comment["message"] = result[4]
        comment["time"] = result[5]
        comment["latitude"] = result[6]
        comment["longitude"] = result[7]
        comment["photo"] = result[8]
        comment["full_name"] = result[9]
        comments.append(comment)
    return comments

def findSubcommentsByPostSeq(commentseq):
    find_subcomments_statement = "select subcomments.*, students.photo, students.full_name, students.status from subcomments,students where subcomments.zid = students.zid and subcomments.commentseq = '" + commentseq + "' order by subcomments.time desc;"
    cu.execute(find_subcomments_statement)
    results = cu.fetchall()
    subcomments=[]
    for result in results:
        if result[10] != 1:
            continue
        subcomment={}
        subcomment["id"] = result[0]
        subcomment["subcommentseq"] = result[1]
        subcomment["commentseq"] = result[2]
        subcomment["zid"] = result[3]
        subcomment["message"] = result[4]
        subcomment["time"] = result[5]
        subcomment["latitude"] = result[6]
        subcomment["longitude"] = result[7]
        subcomment["photo"] = result[8]
        subcomment["full_name"] = result[9]
        subcomments.append(subcomment)
    return subcomments

def newPostseq(zid):
    find_maxPostseq_statement = "select postseq from posts where postseq like '" + zid + "-%'"
    cu.execute(find_maxPostseq_statement)
    results = cu.fetchall()
    maxNumber = 0
    for result in results:
        number = int(result[0].split("-")[1])
        if number > maxNumber:
            maxNumber = number
    newPostseq = zid + "-" + str(maxNumber + 1)
    return newPostseq

def findStudentsByKeyword(keyword):
    find_students_statement = "select zid, full_name, photo, status from students where full_name like '%" + keyword + "%' order by full_name"
    cu.execute(find_students_statement)
    results = cu.fetchall()
    students = []
    for result in results:
        if result[3] !=1 :
            continue
        students.append({"zid":result[0], "full_name":result[1], "photo":result[2]})
    return students
    
def findPostsByKeyword(keyword):
    find_posts_statement = "select students.zid, students.photo, students.full_name, posts.postseq, posts.message, posts.time, posts.latitude, posts.longitude, students.status from posts, students where posts.zid = students.zid and posts.message like '%" + keyword + "%' order by posts.time desc;"
    cu.execute(find_posts_statement)
    results = cu.fetchall()
    posts = []
    for result in results:
        if result[8] != 1:
            continue
        post = {}
        post["zid"] = result[0]
        post["photo"] = result[1]
        post["full_name"] = result[2]
        post["postseq"] = result[3]
        #message = re.sub(r"\\n", "<br>", result[4]
        message = re.sub(r"\"\"", "\"", result[4])
        post["message"] = message
        post["time"] = result[5]
        post["latitude"] = result[6]
        post["longitude"] = result[7]
        posts.append(post)
    return posts

def updateInfo(student):
    set_string = ""
    for item in student:
        if item != "zid" and item != "full_name":
            if student[item] == "":
                set_string += item + " = NULL, "
            elif item == "status" and student[item] == 1:
                set_string += item + " = 1, "
            else:
                set_string += item + " = '" + student[item] + "', "
    set_string += "full_name = '" + student["full_name"] + "'"
    update_info_statement = "update students set " + set_string + " where zid = '" + student["zid"] + "';"
    cu.execute(update_info_statement)
    cx.commit()

def newCommentseq(postseq):
    find_maxCommentseq_statement = "select commentseq from comments where commentseq like '" + postseq + "-%'"
    cu.execute(find_maxCommentseq_statement)
    results = cu.fetchall()
    maxNumber = 0
    for result in results:
        number = int(result[0].split("-")[2])
        if number > maxNumber:
            maxNumber = number
    newCommentseq = postseq + "-" + str(maxNumber + 1)
    return newCommentseq
    
def newSubCommentseq(commentseq):
    find_maxSubCommentseq_statement = "select subcommentseq from subcomments where subcommentseq like '" + commentseq + "-%'"
    cu.execute(find_maxSubCommentseq_statement)
    results = cu.fetchall()
    maxNumber = 0
    for result in results:
        number = int(result[0].split("-")[3])
        if number > maxNumber:
            maxNumber = number
    newSubCommentseq = commentseq + "-" + str(maxNumber + 1)
    return newSubCommentseq
    
def findRelationship(myzid, zid):
    search_friends_statement = "select * from friends where (zid1 = '" + myzid + "' and zid2 = '" + zid + "') or (zid2 = '" + myzid + "' and zid1 = '" + zid + "')"
    search_add_friends_statement = "select * from add_friends where (reqfrom = '" + myzid + "' and reqto = '" + zid + "')"
    cu.execute(search_friends_statement)
    results = cu.fetchall()
    if len(results) > 0 :
        # 1 means relationship is friend
        return 1
    else:
        cu.execute(search_add_friends_statement)
        results = cu.fetchall()
        if len(results) > 0 :
            # 0 means already send friend request
            return 0
        else:
            # -1 means is not friend
            return -1

def findMentions(zid):
    select_mention_statement = "select * from mention where mentionto = '" + zid + "' order by time desc"
    cu.execute(select_mention_statement)
    results = cu.fetchall()
    mentions = []
    for result in results:
        mention={}
        mention["id"] = result[0]
        mention["mentionfrom"] = result[1]
        student = findStudentByZid(result[1])
        mention["full_name"] = student["full_name"]
        mention["photo"] = student["photo"]
        mention["mentionto"] = result[2]
        mention["mentionedplace"] = result[3]
        mention["time"] = result[4]
        
        placeparsing = result[3].split("-")
        mention["postseq"] = placeparsing[0] + "-" + placeparsing[1]
        if len(placeparsing) == 2:
            mention["type"] = "post"
        if len(placeparsing) == 3:
                mention["type"] = "comment"
        if len(placeparsing) == 4:
                mention["type"] = "reply"
        mentions.append(mention)
    return mentions

def findRequests(zid):
    select_requests_statement = "select * from add_friends where reqto = '" + zid + "'"
    cu.execute(select_requests_statement)
    results = cu.fetchall()
    requests = []
    for result in results:
        request={}
        request["id"] = result[0]
        request["reqfrom"] = result[1]
        student = findStudentByZid(result[1])
        request["full_name"] = student["full_name"]
        request["photo"] = student["photo"]
        requests.append(request)
    return requests
    

def send_email(to, subject, message):
    mutt = [
            'mutt',
            '-s',
            subject,
            '-e', 'set copy=no',
            '-e', 'set realname=UNSWtalk',
            '--', to
    ]
    subprocess.run(
            mutt,
            input = message.encode('utf8'),
            stderr = subprocess.PIPE,
            stdout = subprocess.PIPE,
    )


############################# Flask #############################
app = Flask(__name__)

# filter
@app.before_request
def before_request():
    print request.endpoint
    if request.endpoint == 'toLogin':
        return render_template('login.html')
    elif request.endpoint == 'toSendmail':    
        return render_template('sendmail.html')
    elif request.endpoint == 'toRecover':    
        return render_template('recover.html')
    elif request.endpoint == 'sendMail':
        print("send email")
    elif request.endpoint == 'recoverPwd':    
        print("do recover")
    elif request.endpoint == 'toRegister':
        errormsg = request.args.get("errormsg")
        return render_template('register.html',errormsg=errormsg)
    elif request.endpoint == 'register':
        print("go to register")
    elif 'student' in session and session['student']['status'] == 0:
        if request.endpoint == 'toEdit':
            return render_template('edit.html')
        else:
            return render_template('checkemail.html')
    elif 'student' not in session and request.endpoint != 'login':
        return render_template('login.html')

# some static pages
@app.route('/')
@app.route('/toLogin')
def toLogin():
    return render_template('login.html')
    
@app.route('/toEdit')
def toEdit():
    return render_template('edit.html')
    
@app.route('/toPostMessage')
def toPostMessage():
    return render_template('postMessage.html')

@app.route('/toChangePhoto')
def toChangePhoto():
    return render_template('changePhoto.html')
    
@app.route('/toChangeBack')
def toChangeBack():
    return render_template('changeBack.html')
    
@app.route('/toChangePwd')
def toChangePwd():
    return render_template('changePwd.html')
    
@app.route('/toRegister')
def toRegister():
    pass
    
@app.route('/toSendmail')
def toSendmail():
    pass
    
@app.route('/toRecover')
def toRecover():
    pass

# APIs
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    student = findStudentByZid(username)
    if student == 1:
        errormsg = "Account does not exist!"
        return render_template('login.html',errormsg=errormsg)
    elif student == 2:
        errormsg = "Invalid!"
        return render_template('login.html',errormsg=errormsg)
    else:
        if student["password"] == password:
            student.pop("password")
            session['student'] = student
            return redirect(url_for("index"))
        else:
            errormsg = "Incorrect password!"
            return render_template('login.html',errormsg=errormsg)

@app.route('/sendMail', methods=['POST'])
def sendMail():
    zid = request.form.get("username")
    student = findStudentByZid(zid)
    if student == 1:
        errormsg = "Account does not exist!"
        return render_template('sendmail.html',errormsg=errormsg)
    else:
        email = student["email"]
        print(request.url_root)
        # send Email here !!!!!!!!!!!!
    return render_template('checkemail.html') 


@app.route('/recoverPwd', methods=['POST'])
def recoverPwd():
    zid = request.form.get("username")
    password = request.form.get("password")
    update_pwd = "update students set password = '" + password + "' where zid ='" + zid + "'"
    cu.execute(update_pwd)
    cx.commit()
    # send Emial here!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    return render_template('login.html') 


@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get("username")
    full_name = request.form.get("full_name")
    password = request.form.get("password")
    email = request.form.get("email")
    studentofusername = findStudentByZid(username)
    studentofemail = findStudentByEmail(email)
    if studentofusername == 1 and studentofemail == 1:
        insert_student_statement = "insert into students (zid, full_name, password, email, photo, status) values ('" + username +"', '" + full_name + "' , '" + password + "','" + email + "', 'default.png', 0)"
        cu.execute(insert_student_statement)
        cx.commit()
        student = {}
        student["zid"] = username
        student["full_name"] = full_name
        student["email"] = email
        student["status"] = 0
        session['student'] = student
        # send email here !!!!!!!!!!!!!!!!!!!!!!
        return render_template('checkemail.html')
    elif studentofusername != 1 and studentofemail != 1:
        errormsg = "Account already exists!"
        return redirect(url_for("toRegister", errormsg=errormsg))
    elif studentofusername != 1:
        errormsg = "Username already exists!"
        return redirect(url_for("toRegister", errormsg=errormsg))
    else:
        errormsg = "Email already exists!"
        return redirect(url_for("toRegister", errormsg=errormsg))


@app.route('/index')
def index():
    my_session = session.get('student')
    zid = my_session["zid"]
    posts = findPostsByZid(zid)
    return render_template("index.html", posts=posts)
    
    
@app.route('/postMessage', methods=['POST'])
def postMessage():
    message = request.form.get("message")
    my_session = session.get('student')
    zid = my_session["zid"]
    newpostseq = newPostseq(zid)
    current_time  = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    
    zids = re.findall("z[\d]{7}", message)
    for mentionedzid in zids:
        insert_mention_statement = "insert into mention (mentionfrom, mentionto, mentionedplace, time) values ('" + zid + "', '" + mentionedzid + "', '" + newpostseq + "','" + current_time + "')"
        cu.execute(insert_mention_statement)
        cx.commit()
    message = re.sub(r'\'', '\'\'', message)
    message = re.sub(r'\"', '\"\"', message) 
    # send email here !!!!!!!!!!!!!!!!!!!!!!
    
    values = "'" + newpostseq + "', '" + zid + "', '" + message + "', '" + current_time + "'"
    insert_message_statement = "insert into posts (postseq, zid, message, time) values (" + values + ");"
    cu.execute(insert_message_statement)
    cx.commit()
    # send email here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    return redirect(url_for("index"))


@app.route('/postDetail', methods=['GET'])
def postDetail():
    postseq = request.args.get("postseq")
    post = findPostsByPostSeq(postseq)
    comments = findCommentsByPostSeq(postseq)
    for comment in comments:
        commentseq = comment['commentseq']
        subcomments = findSubcommentsByPostSeq(commentseq)
        comment["subcomments"] = subcomments
    post["comments"] = comments
    return render_template('postDetail.html',post=post)


@app.route('/comment', methods=['POST'])
def comment():
    my_session = session.get('student')
    zid = my_session["zid"]
    current_time  = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    toid = request.form.get("toid")
    content = request.form.get("content")
    # send email here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    toidlist = toid.split("-")
    if len(toidlist) == 2:
        commentseq = newCommentseq(toid)
        
        zids = re.findall("z[\d]{7}", content)
        for mentionedzid in zids:
            insert_mention_statement = "insert into mention (mentionfrom, mentionto, mentionedplace, time) values ('" + zid + "', '" + mentionedzid + "', '" + commentseq + "','" + current_time + "')"
            cu.execute(insert_mention_statement)
            cx.commit()
        content = re.sub(r'\'', '\'\'', content)
        content = re.sub(r'\"', '\"\"', content) 
        # send email here !!!!!!!!!!!!!!!!!!!!!!
        values = "'" + commentseq + "', '" + toid + "', '" + zid + "', '" + content + "', '" + current_time + "'"
        insert_comment_statement = "insert into comments (commentseq, postseq, zid, message, time) values (" + values + ");"
        cu.execute(insert_comment_statement)
        postseq = toid
        return redirect(url_for("postDetail", postseq=postseq))
    else:
        subcommentseq = newSubCommentseq(toid)
        
        zids = re.findall("z[\d]{7}", content)
        for mentionedzid in zids:
            insert_mention_statement = "insert into mention (mentionfrom, mentionto, mentionedplace, time) values ('" + zid + "', '" + mentionedzid + "', '" + subcommentseq + "','" + current_time + "')"
            cu.execute(insert_mention_statement)
            cx.commit()
        content = re.sub(r'\'', '\'\'', content)
        content = re.sub(r'\"', '\"\"', content) 
        # send email here !!!!!!!!!!!!!!!!!!!!!!
        values = "'" + subcommentseq + "', '" + toid + "', '" + zid + "', '" + content + "', '" + current_time + "'"
        insert_subcomment_statement = "insert into subcomments (subcommentseq, commentseq, zid, message, time) values (" + values + ");"
        cu.execute(insert_subcomment_statement)
        cx.commit()
        postseq = str(toidlist[0]) + "-" + str(toidlist[1])
        return redirect(url_for("postDetail", postseq=postseq))


@app.route('/profile', methods=['GET'])
def profile():
    zid = request.args.get("zid")
    my_session = session.get('student')
    myzid = my_session["zid"]
    if myzid == zid:
        return redirect("myprofile")
    else:
        # find info
        details = findStudentByZid(zid)
        details.pop("password")
        # find friends
        friends = findFriendsByZid(zid)
        details["friends"] = friends
        # find friend relationship
        relationship = findRelationship(myzid, zid)
        details["relationship"] = relationship
        return render_template('profile.html', details=details)


@app.route('/myprofile')
def myprofile():
    my_session = session.get('student')
    zid = my_session["zid"]
    friends = findFriendsByZid(zid)
    return render_template('myprofile.html',friends=friends)


@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get("keyword")
    selection = request.form.get("selection")
    pattern = re.compile("^\s+$")
    if pattern.match(keyword):
        return redirect(url_for("index"))
    else:
        if selection == "student":
            students = findStudentsByKeyword(keyword)
            return render_template('students.html',students=students)
        else:
            posts = findPostsByKeyword(keyword)
            return render_template('posts.html',posts=posts)


@app.route('/edit', methods=['POST'])
def edit():
    student = {}
    student["zid"] = request.form.get("zid")
    student["full_name"] = request.form.get("full_name")
    student["program"] = request.form.get("program")
    student["email"] = request.form.get("email")
    student["birthday"] = request.form.get("birthday")
    student["home_suburb"] = request.form.get("home_suburb")
    student["courses"] = request.form.get("courses")
    student["profile"] = request.form.get("profile")
    student["status"] = 1
    
    updateInfo(student)
    new_session = findStudentByZid(student["zid"])
    new_session.pop("password")
    session['student'] = new_session
    return redirect(url_for("myprofile"))

@app.route('/changePwd', methods=['POST'])
def changePwd():
    my_session = session.get('student')
    myzid = my_session["zid"]
    password = request.form.get("pwd")
    update_pwd = "update students set password = '" + password + "' where zid ='" + myzid + "'"
    cu.execute(update_pwd)
    cx.commit()
    return redirect(url_for("myprofile"))

@app.route('/changeBack', methods=['POST'])
def changeBack():
    my_session = session.get('student')
    myzid = my_session["zid"]
    file = request.files['background']
    filename = secure_filename(file.filename)
    timestamp = str(time())
    timestamp = re.sub("\.", "", timestamp)
    newfilename = timestamp + filename
    # save file
    file.save(os.path.join('static', 'background', newfilename))
    # update database
    update_back = "update students set background = '" + newfilename + "' where zid ='" + myzid + "'"
    cu.execute(update_back)
    cx.commit()
    new_session = findStudentByZid(myzid)
    new_session.pop("password")
    session['student'] = new_session
    return redirect(url_for("myprofile"))
    

@app.route('/chanegPhoto', methods=['POST'])
def chanegPhoto():
    my_session = session.get('student')
    myzid = my_session["zid"]
    file = request.files['photo']
    filename = secure_filename(file.filename)
    timestamp = str(time())
    timestamp = re.sub("\.", "", timestamp)
    newfilename = timestamp + filename
    # save file
    file.save(os.path.join('static', 'photos', newfilename))
    # update database
    update_photo = "update students set photo = '" + newfilename + "' where zid ='" + myzid + "'"
    cu.execute(update_photo)
    cx.commit()
    new_session = findStudentByZid(myzid)
    new_session.pop("password")
    session['student'] = new_session
    return redirect(url_for("myprofile"))


@app.route('/friend', methods=['GET'])
def friend():
    zid = request.args.get("zid")
    my_session = session.get('student')
    myzid = my_session["zid"]
    # if he has already send request to me and you want to add him to, then you became friends
    # else just send request!
    check_statement = "select * from add_friends where reqfrom = '" + zid + "' and reqto = '" + myzid + "'"
    cu.execute(check_statement)
    results = cu.fetchall()
    if len(results) == 1:
        delete_statement = "delete from add_friends where reqfrom = '" + zid + "' and reqto = '" + myzid + "'"
        cu.execute(delete_statement)
        confirm_statement = "insert into friends (zid1, zid2) values ('" + myzid + "', '" + zid + "')"
        # send email here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        cu.execute(confirm_statement)
    else:
        friend_statement = "insert into add_friends (reqfrom, reqto) values ('" + myzid + "', '" + zid + "')"
        # send email here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        cu.execute(friend_statement)
    cx.commit()
    return redirect(url_for("profile",zid=zid))


@app.route('/unfriend', methods=['GET'])
def unfriend():
    zid = request.args.get("zid")
    my_session = session.get('student')
    myzid = my_session["zid"]
    unfriend_statement = "delete from friends where (zid1 = '" + zid + "' and zid2 = '" + myzid + "') or (zid1 = '" + myzid + "' and zid2 = '" + zid + "')"
    cu.execute(unfriend_statement)
    cx.commit()
    return redirect(url_for("profile",zid=zid))

@app.route('/reject', methods=['GET'])
def reject():
    zid = request.args.get("zid")
    my_session = session.get('student')
    myzid = my_session["zid"]
    reject_statement = "delete from add_friends where reqfrom = '" + zid + "' and reqto = '" + myzid + "'"
    cu.execute(reject_statement)
    cx.commit()
    return redirect(url_for("notification"))

@app.route('/accept', methods=['GET'])
def accept():
    zid = request.args.get("zid")
    my_session = session.get('student')
    myzid = my_session["zid"]
    delete_statement = "delete from add_friends where reqfrom = '" + zid + "' and reqto = '" + myzid + "'"
    cu.execute(delete_statement)
    confirm_statement = "insert into friends (zid1, zid2) values ('" + myzid + "', '" + zid + "')"
    cu.execute(confirm_statement)
    cx.commit()
    # send email here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    return redirect(url_for("notification"))


@app.route('/notification')
def notification():
    my_session = session.get('student')
    myzid = my_session["zid"]
    mentions = findMentions(myzid)
    friendrequests = findRequests(myzid)
    return render_template('notification.html',mentions=mentions,requests=friendrequests)
    

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
