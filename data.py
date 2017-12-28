from sqlite3 import *
from time import time, ctime

data = connect('data.db')
data.row_factory = Row
cursor = data.cursor()

#table creation
try:
    cursor.execute('create table settings(token text,debugch integer)')
except OperationalError:
    pass  #table exist

#table creation
try:
    cursor.execute('create table sourcers(channel text,name text unique,lastpost integer)')
except OperationalError:
    pass  #table exist

def settings_edit():
    token = input('Enter token: ')
    debugch = input('Enter debug channel: ')
    cursor.execute('insert into settings values(?,?)', (token, debugch))
    data.commit()    

def settings_check(): 
    try:
        params = dict(cursor.execute('select * from settings').fetchall()[0])
    except IndexError:
        params = dict(cursor.execute('select * from settings').fetchall())
    return params

params = settings_check()
if not params:
    settings_edit()
    
def sourcers_check():
    try:
        sourcers = [dict(x) for x in  cursor.execute('select * from sourcers').fetchall()]
    except IndexError:
        pass
        #sourcers = dict(cursor.execute('select * from sourcers').fetchall())
    return sourcers

def sourcers_add():
    while True:
        print("Send '###' to exit")
        chat = input('Enter chat: ')
        if chat == '###':
            break
        source = input('Enter source: ')
        if source == '###':
            break
        cursor.execute(
            'insert into sourcers values(?,?,?)', (chat, source, time())
        )
        data.commit()

def sourcers_update(name, lastpost):
    cursor.execute('update sourcers set lastpost=? where name=?',
                   (lastpost, name))
    data.commit()

sourcers = sourcers_check()
if not sourcers:
    sourcers_add()