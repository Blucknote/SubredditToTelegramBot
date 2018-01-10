from redditsaver import reddit as rsave
from tgapi import api
from tgkeyboard import keyboard
from sys import argv
from urllib.request import urlopen, quote
import data

if len(argv) > 1:
    if argv[1] == 'add':
        data.sourcers_add()
    if argv[1] == 'settings':
        data.settings_edit()

def retry(fn):
    def wrapper(addr, retries = 10, i:"counter" = 0):
        while i < retries:
            try:
                fn(addr)
            except:
                i += 1
            else:
                break
    return wrapper

def is_photo(string):
    return string.split('.')[-1] in ['jpg', 'jpeg', 'png']

def prepare(post: list, channel: str):
    def processing(post):
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


        if not is_photo(post['url']):        #domain or gif
            media = rsave.process_domains(post['url'])

            *links, = map(
                lambda x:dict(
                    url = x,
                    kb = '&reply_markup=%s' % keyboard.build(kb),
                    caption = '&caption=%s' % quote(post['title']),
                    channel = channel                    
                ), media                
            )
            return links
        
        else:                               #jpg
            return [
                dict(url = post['url'],
                     caption = '&caption=%s' % quote(post['title']),
                     kb = '&reply_markup=%s' % keyboard.build(kb),
                     channel = channel)                
            ] 

    *prepared, = map(processing, map(lambda x: x['data'], post))
    *sending, = map(sender, filter(lambda x: x is not None, prepared))

def sender(prepared: list):
    @retry
    def inner(addr):
        urlopen(addr)
    
    for prep in prepared:
        method = 'sendPhoto?' if is_photo(prep['url']) else 'sendVideo?'
        mediaType = '&photo=%s' if is_photo(prep['url']) else '&video=%s'

        addr = {
            'api': api.domain % data.params['token'],
            'method': method,
            'channel': 'chat_id=%s' % prep['channel'],
            'type': mediaType % prep['url'],
            'caption': prep['caption'],
            'kb': prep['kb'],            
        }

        inner('{api}{method}{channel}{type}{caption}{kb}'.format(**addr))
    

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

            if post:     #check for newer posts exist
                prepare(post, reddit['channel'] if not debug else data.params['debugch'])
                reddit['lastpost'] = max(
                    map(lambda x:x['data']['created'],post)
                )
        
        data.sourcers_update(reddit['name'], reddit['lastpost'])

get_posts(data.sourcers, debug= True)