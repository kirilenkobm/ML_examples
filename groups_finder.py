import requests
from settings import token, my_id, api_v
import json

URL = "https://api.vk.com/method/groups.search"  # API method URL
URL2 = "https://api.vk.com/method/groups.getById"

offset = 0  #
count = 100  # MAX value = 1000

""""
Script extracts VK.groups id's according your search query
Saves id's to the txt file
"""


def request(query):
    r = requests.get(URL, params={
                     'access_token': token,
                     'q': query,
                     'type': 'group',
                     'count': count,
                     'sort': 3
                     })  # groups query
    data = json.loads(r.text)  # распарсиваем json
    names = []
    for i in range(1, count+1):
        try:
            if data['response'][i]['is_closed'] == 0:
                names.append(data['response'][i]['screen_name'])
            else:
                pass  # if closed - ignore
        except Exception:
            break  # if response < count
    return names

# main script
Repeat = True
while Repeat:
    groups = []
    query = input('Query: ')
    groups = request(query)
    with open('groupslist.txt', 'a') as f:
        for x in groups:
            out = str(x) + ' '
            f.write(out)
    with open('groups_queries.txt', 'a') as f:
        out = query + '\n'
        f.write(out)
    print('repeat? Y/N')
    rep = input(' ')
    if rep == 'N' or rep == 'n' or rep == 'no' or rep == 'No':
        Repeat = False
