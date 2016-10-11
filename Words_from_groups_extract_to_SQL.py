import requests
from settings import token, translit
import re
import pymorphy2
import json
import sqlite3
from datetime import datetime as dt

"""
This script extracts text data from VK communities list
and enters obtained data in SQLite db
"""

# script initiation
inputflag = input('Communities from text file (Y\default) or console input (N)? ')
if inputflag == 'N':
    group_input = input('Group ids: ')
    group_ids = group_input.split()
else:
    with open('groupslist.txt', 'r') as f:
        group_ids = str(f.readlines()[0]).split()
        group_ids = list(set(group_ids))
        for i in group_ids:
            if i.startswith("club"):
                group_ids.remove(i)
start_time = dt.now()

# db connection
conn = sqlite3.connect('textarray.db')
cur = conn.cursor()

# two tables - for training and validation
Train = True
if Train:
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS train(
            cat TINYINT,
            name VARCHAR,
            description TEXT,
            words TEXT);""")

if not Train:  # создадим тестовую ссылку
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS test(
            cat TINYINT,
            name VARCHAR,
            description TEXT,
            words TEXT);""")

# constants
URL = "https://api.vk.com/method/"  # API methods URL
morph = pymorphy2.MorphAnalyzer()
co = 100  # count of wall.posts, max value = 100
consola = False  # console output
csvout = False  # csv output
sqldb = True  # SQL output


# text extraction func
def wall_extractor(group_id):
    r = requests.get(URL+'wall.get',
                     params={'access_token': token,
                             'domain': group_id,
                             'count': co,
                             'extended': 0})  # реквест стены

    walljs = json.loads(r.text)  # переводим посты в json
    wordslst = []
    for i in range(1, co+1):  # i - номер поста с единицы
        try:
            wordslst.append(walljs['response'][i]['text'])  # собираем слова в один список
        except Exception:
            break
    wordsstr = ' '.join(wordslst)
    wordsstr = wordsstr.lower().replace('br', ' ')  # делаем ловеркейз обеим строкам
    wordsstr = re.sub(r'[^\w\s]+|[\d]+]', r' ', wordsstr)  # и чистим спецсимволы
    return wordsstr


# group description extractor
def descr_extractor(group_id):
    r2 = requests.get(URL + 'groups.getById',
                      params={'group_ids': group_id,
                              'access_token': token,
                              'fields': 'description'})   # реквест описания
    try:
        descjs = json.loads(r2.text)  # переводим описание в json
        description = str(descjs['response'][0]['description'])  # распарсенное описание
        description = description.lower().replace('br', ' ')  # и тут тоже чистим спецсимволы
        description = re.sub(r'[^\w\s]+|[\d]+]', r' ', description)
        print('Text data from {0} extracted.'.format(group_id))  # чтобы видеть, что процесс идет
    except Exception:
        description = 'void'
        print('Text data from {0} extracted without description'.format(group_id))
    return description


# words transformation to normal morph form
def langmeth(text):
    words = []
    for word in text:
        normal_word = morph.parse(word)[0].normal_form  # приведение всех слов к одной форме
        words.append(normal_word)
    return words  # приходится вернуть словарь


# group size extraction (throw out the empty community)
def groupsize(group_id):
    r = requests.get(URL + 'groups.getById',
                     params={'group_id': group_id,
                             'fields': 'members_count'})
    try:
        closed = int((json.loads(r.text)['response'][0]['is_closed']))
        if closed == 1 or closed == 2:  # filter for private and banned groups
            size = 0
        else:
            size = int((json.loads(r.text)['response'][0]['members_count']))
    except Exception:
        size = 0
    return size

# main script
for group_id in group_ids:
    if groupsize(group_id) > 1000:
        raw_text_1 = wall_extractor(group_id)
        postlst = langmeth(raw_text_1.split(' '))
        postcyr = ' '.join(postlst)
        raw_text_2 = descr_extractor(group_id)
        desclst = langmeth(raw_text_2.split(' '))
        desccyr = ' '.join(desclst)
        postlat = translit(postcyr)  # transliterate cyr to lat,
        desclat = translit(desccyr)  # csv format required

        if consola:  # console output
            print('Description:\n{0}\nWords:\n{1}'.format(desccyr, postcyr))

        if csvout:  # csv output
            s1 = group_id
            s1 += ';'
            s2 = desclat
            s2 += ';'
            s3 = postlat
            s3 += '\n'
            output = s1 + s2 + s3
            with open('data.csv', 'a', encoding='utf-8') as f:
                f.write(output)

        if sqldb:  # SQL output
            outtext = postcyr[:65535]
            if Train:
                cur.execute("DELETE FROM train WHERE name=?", (group_id, ))
                cur.execute("INSERT INTO train(cat, name, description, words) VALUES(?, ?, ?, ?)",
                            (-1, group_id, desccyr, outtext))
            if not Train:
                cur.execute("DELETE FROM test WHERE name=?", (group_id,))
                cur.execute("INSERT INTO test(cat, name, description, words) VALUES(?, ?, ?, ?)",
                            (-1, group_id, desccyr, outtext))
        else:
            pass

cur.close()
conn.commit()
print('Estimated time: {0}'.format(dt.now() - start_time))
