# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os
import re
import sqlite3
from flask import Flask, render_template, session


############################# initial database #############################
students_dir = "dataset-medium";
# some table names
students_table = "students"
# create a database
#cx = sqlite3.connect('./UNSWtalk.db')
cx = sqlite3.connect(":memory:", check_same_thread = False)
cu = cx.cursor()

drop_students_table = "drop table if exists " + students_table
create_students_table = "create table if not exists " + students_table + "(id INTEGER not null primary key AUTOINCREMENT, zid text not null, password text not null, full_name text, program text, courses text, email text, birthday text, friends text, home_longitude text, home_latitude text, home_suburb text)"

def initDatabase():
    cu.execute(drop_students_table)
    cu.execute(create_students_table)
    
    students = sorted(os.listdir(students_dir))
    for student in students:
        if re.match(r'^\..+', student):
            continue
        details_filename = os.path.join(students_dir, student, "student.txt")
        with open(details_filename) as f:
            info_flow = f.read()
            details = info_flow.split('\n')
            details = list(filter(lambda x: x != "", details))
            insert_info_statement = "insert into " + students_table
            keys = ""
            values = ""
            for i in range(len(details)):
                key = details[i].split(": ", 1)[0]
                value = details[i].split(": ", 1)[1]
                if i != len(details)-1:
                    keys += str(key) + ","
                    values += "\"" + str(value) + "\","
                else:
                    keys += str(key)
                    values += "\"" + str(value) + "\""
            insert_info_statement += "(" + keys + ") values (" + values + ");"
            cu.execute(insert_info_statement)


############################# Flask #############################
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
def start():
#    n = session.get('n', 0)
#    students = sorted(os.listdir(students_dir))
#    student_to_show = students[n % len(students)]
#    details_filename = os.path.join(students_dir, student_to_show, "student.txt")
#    with open(details_filename) as f:
#        details = f.read()
#    session['n'] = n + 1
#    return render_template('start.html', student_details=details)
    n = session.get('n', 1)
    show_info_statement = "select zid, full_name, birthday, friends, program, home_suburb from students where id = " + str(n)
    cu.execute(show_info_statement)
    info = cu.fetchone()
    details = {}
    details["zid"] = info[0]
    details["full_name"] = info[1]
    details["birthday"] = info[2]
    details["friends"] = info[3]
    details["program"] = info[4]
    details["home_suburb"] = info[5]
    session['n'] = n + 1
    return render_template('start.html', student_details=details)

if __name__ == '__main__':
    initDatabase()
    app.secret_key = os.urandom(12)
    app.run(debug=True)
