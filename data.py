from sqlite3 import *
from time import time, ctime

data = connect('data.db')
data.row_factory = Row
cursor = data.cursor()

#table creation
try:
    cursor.execute('create table sourcers(channel text,name text unique,lastpost integer)')
except OperationalError:
    pass  #table exist

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


sourcers = [
    dict(x) for x in  cursor.execute('select * from sourcers').fetchall()
]
if __name__ == '__main__':
    if not sourcers:
        sourcers_add()