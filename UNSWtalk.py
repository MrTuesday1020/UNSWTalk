# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os
import re
import sqlite3
from flask import Flask, render_template, session, request, redirect
from shutil import copyfile
from time import gmtime, strftime

############################# initial database and store data #############################
# dataset
students_dir = "dataset-medium";
# some table names
students_table = "students"
friends_table = "friends"
add_friends_table = "addfriends"
posts_table = "posts"
comments_table = "comments"
subcomments_table = "subcomments"

# create a database
# cx = sqlite3.connect('./UNSWtalk.db')
cx = sqlite3.connect(":memory:", check_same_thread = False)
cu = cx.cursor()
cu.execute("PRAGMA busy_timeout = 30000")

def initDatabase():
    # some sql statements
    drop_students_table = "drop table if exists students"
    drop_friends_table = "drop table if exists friends"
    drop_add_friends_table = "drop table if exists add_friends"
    drop_posts_table = "drop table if exists posts"
    drop_comments_table = "drop table if exists comments"
    drop_subcomments_table = "drop table if exists subcomments"

    create_students_table = "create table if not exists students (id INTEGER not null primary key AUTOINCREMENT, zid text not null, password text not null, photo text not null, full_name text, program text, courses text, email text, birthday text, home_longitude text, home_latitude text, home_suburb text)"
    create_friends_table = "create table if not exists friends (id INTEGER not null primary key AUTOINCREMENT, zid1 text not null, zid2 text not null)"
    create_add_friends_table = "create table if not exists add_friends (id INTEGER not null primary key AUTOINCREMENT, reqfrom text not null, reqto text not null)"
    create_posts_table = "create table if not exists posts (id INTEGER not null primary key AUTOINCREMENT, postseq text not null, zid text not null, message text not null, time text not null, latitude text, longitude text)"
    create_comments_table = "create table if not exists comments (id INTEGER not null primary key AUTOINCREMENT, commentseq text not null, postseq text not null, zid text not null, message text, time text not null, latitude text, longitude text)"
    create_subcomments_table = "create table if not exists subcomments (id INTEGER not null primary key AUTOINCREMENT, subcommentseq text not null, commentseq text not null, zid text not null, message text, time text not null, latitude text, longitude text)"

    # create tables
    #cu.execute(drop_students_table)
    cu.execute(create_students_table)
    #cu.execute(drop_friends_table)
    cu.execute(create_friends_table)
    #cu.execute(drop_add_friends_table)
    cu.execute(create_add_friends_table)
    #cu.execute(drop_posts_table)
    cu.execute(create_posts_table)
    #cu.execute(drop_comments_table)
    cu.execute(create_comments_table)
    #cu.execute(drop_posts_table)
    cu.execute(create_subcomments_table)
    
    
    # store details and friends
    friends_list = []
    students = sorted(os.listdir(students_dir))
    for student in students:
        if re.match(r'^\..+', student):
            continue
        details_filename = os.path.join(students_dir, student, "student.txt")
        with open(details_filename) as f:
            info_flow = f.read()
            details = info_flow.split('\n')
            details = list(filter(lambda x: x != "", details))
            keys = ""
            values = ""
            for detail in details:
                key = detail.split(": ", 1)[0]
                value = detail.split(": ", 1)[1]
                if key == "friends":
                    friends = re.findall("z\d+", value)
                    for friend in friends:
                        friend_tuple = (student, friend)
                        friends_list.append(friend_tuple)
                else:
                    keys += str(key) + ","
                    values += "\"" + str(value) + "\","
        src_photo = os.path.join(students_dir, student, "img.jpg")
        if os.path.isfile(src_photo):
            new_phtot_name = str(student) + ".jpg"
            dst_photo = os.path.join("static", "photos", new_phtot_name)
            copyfile(src_photo,dst_photo)
            keys += "photo" 
            values += "\"" + new_phtot_name + "\""
        else:
            keys += "photo" 
            values += "\"default.png\""
        # insert student info into database one by one
        insert_info_statement = "insert into students (" + keys + ") values (" + values + ");"
        cu.execute(insert_info_statement)
    
    # split friends_list into added_friends and add_friends
    added_friends = []
    add_friends = []
    for item in friends_list:
        # if they want to add each other then they are friends already
        temp = (item[1], item[0])
        if temp in friends_list:
            if temp not in added_friends:
                added_friends.append(item)
        else:
            add_friends.append(item)
    
    # insert friends into database one by one
    for friends in added_friends:
        insert_friends_statement = "insert into friends (zid1, zid2) values (\"" + friends[0] + "\", \"" +  friends[1] + "\");"
        cu.execute(insert_friends_statement)
    # insert add friend requests into database one by one
    for request in add_friends:
        insert_add_friends_statement = "insert into add_friends (reqfrom, reqto) values (\"" + request[0] + "\", \"" +  request[1] + "\");"
        cu.execute(insert_add_friends_statement)
       
    # store messages
    for student in students:
        if re.match(r'^\..+', student):
            continue
        studentsdires = os.path.join(students_dir, student)
        files = sorted(os.listdir(studentsdires))
        for file in files:
            if re.match(r'^\d+.+', file):
                post_filename = os.path.join(students_dir, student, file)
                with open(post_filename) as f:
                    post_flow = f.read()
                    post_details = post_flow.split('\n')
                    post_details = list(filter(lambda x: x != "", post_details))
                    post = {}
                    for line in post_details:
                        key = line.split(": ", 1)[0]
                        value = line.split(": ", 1)[1]
                        #if key == "message":
                        #    print value
                        if key == "message":
                            value = re.sub(r'\'', '\'\'', value) 
                            value = re.sub(r'\"', '\"\"', value) 
                        if key == "from":
                            post["zid"] = value
                        elif key == "time":
                            value = value.split("+")[0]
                            value = re.sub(r'T', ' ', value) 
                            post[key] = value
                        else:
                            post[key] = value
                    #print post
                
                    columns = ""
                    values = ""
                    for key in post:
                        columns += key + ", "
                        values += "'" + post[key] + "', "
                    
                    seq = file.split(".")[0]
                    filename = seq.split("-")
                    if len(filename) == 1:
                        postseq = student + "-" + filename[0]
                        columns += "postseq"
                        values += "'" + postseq + "'"
                        insert_post_statement = "insert into posts (" + columns + ") values (" + values + ");"
                        #print insert_post_statement
                        cu.execute(insert_post_statement)
                    elif len(filename) == 2:
                        postseq = student + "-" + filename[0]
                        columns += "postseq, "
                        values += "'" + postseq + "', "
                        commentseq = student + "-" + filename[0] + "-" + filename[1]
                        columns += "commentseq"
                        values += "'" + commentseq + "'"
                        insert_comments_statement = "insert into comments (" + columns + ") values (" + values + ");"
                        #print insert_post_statement
                        cu.execute(insert_comments_statement)
                    elif len(filename) == 3:
                        commentseq = student + "-" + filename[0] + "-" + filename[1]
                        columns += "commentseq, "
                        values += "'" + commentseq + "', "
                        subcommentseq = student + "-" + filename[0] + "-" + filename[1] + "-" + filename[2]
                        columns += "subcommentseq"
                        values += "'" + subcommentseq + "'"
                        insert_subcomments_statement = "insert into subcomments (" + columns + ") values (" + values + ");"
                        #print insert_post_statement
                        cu.execute(insert_subcomments_statement)
                    else:
                        print "valid posts!"
                        continue
            else:
                continue 
    
#    find_student_statement = "select message from subcomments where subcommentseq = 'z5190454-13-13-0'"
#    cu.execute(find_student_statement)
#    result = cu.fetchall()
#    print result
    #print strftime("%Y-%m-%d %H:%M:%S", gmtime())
    print "Database initialized done!"


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
        return student


def findFriendsByZid(zid):
    friends = []
    find_freinds_statement = "select friends.zid2, students.photo, students.full_name from friends, students where friends.zid1 = \"" + zid + "\" and friends.zid2 = students.zid union select friends.zid1, students.photo, students.full_name from friends, students where friends.zid2 = \"" + zid + "\" and friends.zid1 = students.zid;"
    cu.execute(find_freinds_statement)
    results = cu.fetchall()
    for result in results:
        friends.append({"zid":result[0], "photo":result[1], "full_name":result[2]})
    return friends


def findPostsByZid(zid):
    friends = findFriendsByZid(zid)
    zids = ""
    for friend in friends:
        zids += "'" + friend["zid"] + "', "
    zids += "'" + zid + "'"
    find_posts_statement = "select students.zid, students.photo, students.full_name, posts.postseq, posts.message, posts.time, posts.latitude, posts.longitude from posts, students where posts.zid = students.zid and posts.zid in (" + zids + ") order by posts.time desc;"
    cu.execute(find_posts_statement)
    results = cu.fetchall()
    posts = []
    for result in results:
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
    find_comments_statement = "select comments.*, students.photo, students.full_name from comments,students where comments.zid = students.zid and comments.postseq = '" + postseq + "' order by comments.time desc;"
    cu.execute(find_comments_statement)
    results = cu.fetchall()
    comments=[]
    for result in results:
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
    find_subcomments_statement = "select subcomments.*, students.photo, students.full_name from subcomments,students where subcomments.zid = students.zid and subcomments.commentseq = '" + commentseq + "' order by subcomments.time desc;"
    cu.execute(find_subcomments_statement)
    results = cu.fetchall()
    subcomments=[]
    for result in results:
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

def newPostseqByZid(zid):
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
    find_students_statement = "select zid, full_name, photo from students where full_name like '%" + keyword + "%' order by full_name"
    cu.execute(find_students_statement)
    results = cu.fetchall()
    students = []
    for result in results:
        students.append({"zid":result[0], "full_name":result[1], "photo":result[2]})
    return students
    
def findPostsByKeyword(keyword):
    find_posts_statement = "select students.zid, students.photo, students.full_name, posts.postseq, posts.message, posts.time, posts.latitude, posts.longitude from posts, students where posts.zid = students.zid and posts.message like '%" + keyword + "%' order by posts.time desc;"
    cu.execute(find_posts_statement)
    results = cu.fetchall()
    posts = []
    for result in results:
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



############################# Flask #############################
app = Flask(__name__)

#@app.before_request
#def before_request():
#    if 'student' not in session and request.endpoint != 'login':
#        errormsg = "Please log in!"
#        return render_template('login.html',errormsg=errormsg)


@app.route('/')
def init():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    student = findStudentByZid(username)
    if student == 1:
        errormsg = "Account doesn't exist!"
        return render_template('login.html',errormsg=errormsg)
    elif student == 2:
        errormsg = "Invalid!"
        return render_template('login.html',errormsg=errormsg)
    else:
        if student["password"] == password:
            student.pop("password")
            session['student'] = student
            return redirect("/index")
        else:
            errormsg = "Incorrect password!"
            return render_template('login.html',errormsg=errormsg)


@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')


@app.route('/index')
def index():
    my_session = session.get('student')
    zid = my_session["zid"]
    posts = findPostsByZid(zid)
    return render_template("index.html", posts=posts)


@app.route('/toPostMessage')
def toPostMessage():
    return render_template('postMessage.html')
    
    
@app.route('/postMessage', methods=['POST'])
def postMessage():
    message = request.form.get("message")
    my_session = session.get('student')
    zid = my_session["zid"]
    newPostseq = newPostseqByZid(zid)
    current_time  = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    values = "'" + newPostseq + "', '" + zid + "', '" + message + "', '" + current_time + "'"
    insert_message_statement = "insert into posts (postseq, zid, message, time) values (" + values + ");"
    print insert_message_statement
    cu.execute(insert_message_statement)
    return redirect("/index")


@app.route('/postDetail')
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


@app.route('/profile', methods=['GET'])
def profile():
    zid = request.args.get("zid")
    # find info
    details = findStudentByZid(zid)
    details.pop("password")
    # find friends
    friends = findFriendsByZid(zid)
    details["friends"] = friends
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
        return redirect("/index")
    else:
        if selection == "student":
            students = findStudentsByKeyword(keyword)
            return render_template('students.html',students=students)
        else:
            posts = findPostsByKeyword(keyword)
            return render_template('posts.html',posts=posts)
    
    
#@app.route('/start', methods=['GET','POST'])
#def start():
#    n = session.get('n', 1)
#    # find info
#    find_info_statement = "select zid, full_name, birthday, program, home_suburb, photo from students where id = " + str(n) + ";"
#    cu.execute(find_info_statement)
#    info = cu.fetchone()
#    details = {}
#    details["zid"] = info[0]
#    details["full_name"] = info[1]
#    details["birthday"] = info[2]
#    details["program"] = info[3]
#    details["home_suburb"] = info[4]
#    details["photo"] = info[5]
#    details["friends"] = []
#    # find friends
#    find_freinds_statement = "select friends.zid2, students.photo from friends, students where friends.zid1 = \"" + info[0] + "\" and friends.zid2 = students.zid union select friends.zid1, students.photo from friends, students where friends.zid2 = \"" + info[0] + "\" and friends.zid1 = students.zid;"
#    cu.execute(find_freinds_statement)
#    friends = cu.fetchall()
#    for friend in friends:
#        details["friends"].append({"zid":friend[0],"photo":friend[1]})
#    session['n'] = n + 1
#    return render_template('start.html', student_details=details)



if __name__ == '__main__':
    initDatabase()
    app.secret_key = os.urandom(12)
    app.run(debug=True)
