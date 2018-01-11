from redditsaver import reddit as rsave
from tgapi import api
from tgkeyboard import keyboard
from sys import argv
from urllib.request import urlopen, quote
import data
import re

photo = re.compile(r'jpe?g|png')

def is_photo(string):
    return re.findall(photo, string)

def send(url, channel, text = '', reply = ''):
    #jpg
    if is_photo(url):
        api.send_photo(
            data.params['token'],
            channel,
            url,
            '', 
            reply
        )
    #gif
    elif url.endswith('.gif'):
        api.send_document(
            data.params['token'],
            channel,
            url,
            '',
            reply
        )
    #video
    elif url.split('.')[-1] in ['mp4', 'gifv', 'WebM']:
        api.send_video(
            data.params['token'],
            channel,
            url,
            '',
            reply
        )
    #domain
    else:
        media = rsave.process_domains(url)
        if media:
            if len(media) > 1:
                api.send_media_group(
                    data.params['token'],
                    channel,
                    media
                )
                #because in api you cant send keyboard with media group
                api.send_message(
                    data.params['token'],
                    channel,
                    text,
                    reply
                )
            else:
                send(media.pop(), channel, text, reply)   

def prepare(posts: list, channel: str or int):
    for post in [x['data'] for x in posts]:
        domain = 'https://www.reddit.com'
        kb = keyboard.create(3, True)
        kbrow = kb['inline_keyboard']
        kbrow[0].append(
            keyboard.button(
                kb,
                post['subreddit'],
                '%s/r/%s' % (domain, post['subreddit'])
            )
        )

        kbrow[1].append(
            keyboard.button(
                kb,
                post['author'],
                '%s/user/%s/submitted' % (domain, post['author'])
            )
        )
        kbrow[2].append(
            keyboard.button(kb,
                            'Подписаться',
                            'https://telegram.me/redditchanelbot?start=%s'
                            % post['author'])
        )
        send(post['url'], channel, post['title'] , keyboard.build(kb))

def get_posts(_data:dict, user = False, debug = False):
    domain = 'https://www.reddit.com/'
    for dat in _data:
        dat['link'] = '%sr/%s.json' % (domain, dat['name'])
        dat['user'] = '%suser/%s/submitted.json' % (domain, dat['name'])                       
    newtime = {}

    for reddit in _data:
        if user:
            posts = rsave.get(reddit['user'])
        else:
            posts = rsave.get(reddit['link'])

        if posts is not None:
            *post, = filter(
                lambda newtime, oldtime = float(reddit['lastpost']):
                newtime['data']['created'] > oldtime, posts                
            )
            
            #check for newer posts exist
            if post:              
                prepare(
                    post,
                    reddit['channel'] if not debug else data.params['debugch']
                )
                
                reddit['lastpost'] = max(
                    map(lambda x:x['data']['created'],post)
                )
        
        data.sourcers_update(reddit['name'], reddit['lastpost'])

if len(argv) > 1:
    if argv[1] == 'add':
        data.sourcers_add()
    if argv[1] == 'settings':
        data.settings_edit()
    if argv[1] == 'debug':
        get_posts(data.sourcers, debug= True)

get_posts(data.sourcers)