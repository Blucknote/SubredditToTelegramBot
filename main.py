from redditsaver import reddit as rsave
from sys import argv
from urllib.request import urlopen, quote
import data
import tgbot.main as bot
import re

photo = re.compile(r'jpe?g|png')

def is_photo(string):
    return re.findall(photo, string)

def send(url, channel, text = '', reply = ''):
    #jpg
    if is_photo(url):
        bot.send_photo(channel, url, text, reply)
    
    #gif
    elif url.endswith('.gif'):
        bot.send_document(channel, url, text, reply)
    
    #video
    elif url.split('.')[-1] in ['mp4', 'gifv', 'WebM']:
        bot.send_video(channel, url, text, reply)
    
    #domain
    else:
        media = rsave.process_domains(url)
        if media:
            if len(media) > 1:
                bot.send_media_group(channel, media)
                
                #because in api you cant send keyboard with media group
                bot.send_message(channel, text, reply)
            else:
                send(media.pop(), channel, text, reply)   

def prepare(posts: list, channel: str or int):
    for post in [x['data'] for x in posts]:
        domain = 'https://www.reddit.com'
        post_keyboard = bot.Keyboard(inline = True, rows= 3)
        
        post_keyboard.add_button(
            0,
            caption= post['subreddit'],
            link= '%s/r/%s' % (domain, post['subreddit'])
        )
        
        post_keyboard.add_button(
            1,
            caption= post['author'],
            link= '%s/user/%s/submitted' % (domain, post['author'])            
        )
        
        post_keyboard.add_button(
            2,
            caption= 'Подписаться',
            link= 'https://telegram.me/redditchanelbot?start=%s'
            % post['author']            
        )
        send(post['url'], channel, quote(post['title']) , post_keyboard)

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
            post = [
                *filter(
                    lambda newtime, oldtime = float(reddit['lastpost']):
                    newtime['data']['created'] > oldtime, posts                 
                )                
            ]
            
            #check for newer posts exist
            if post:              
                prepare(
                    post,
                    reddit['channel'] if not debug else '106989752'
                )
                
                reddit['lastpost'] = max(
                    map(lambda x:x['data']['created'],post)
                )
        
        data.sourcers_update(reddit['name'], reddit['lastpost'])

if len(argv) > 1:
    if argv[1] == 'add':
        data.sourcers_add()
    if argv[1] == 'debug':
        get_posts(data.sourcers, debug= True)

get_posts(data.sourcers)