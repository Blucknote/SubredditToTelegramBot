import configparser
from sys import argv
from urllib.request import urlopen
from redditsaver import reddit as rsave
from tgapi import api
from tgkeyboard import keyboard
from settings import debugch

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

def read_settings(fname):
    c = configparser.ConfigParser()
    c.read(fname)
    for lastpost in c['sourcers']:
        if not c['sourcers'][lastpost]:
            from time import time
            c['sourcers'][lastpost] = '%s' % time()
    with open(fname, 'w') as configfile:
        c.write(configfile)            
    return {'channel': c['channel']['name'],
            'src': dict(c.items('sourcers'))}

def save_settings(fname, update):
    c = configparser.ConfigParser()
    c.read(fname)
    c['sourcers'] = update
    with open(fname, 'w') as configfile:
        c.write(configfile)

def source(d):
    domain = 'https://www.reddit.com/'
    ret = []
    for name in d:
        ret.append(
            {
                'name': '%s' % name,
                'link': '%sr/%s.json' % (domain, name),
                'user': '%suser/%s/submitted.json' % (domain, name),
                'lastpost': d[name]                
            }            
        )
    return ret

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
            media = redditsaver.process_domains(post['url'])

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
            'api': api.domain,
            'method': method,
            'channel': 'chat_id=%s' % prep['channel'],
            'type': mediaType % prep['url'],
            'caption': prep['caption'],
            'kb': prep['kb'],            
        }

        inner('{api}{method}{channel}{type}{caption}{kb}'.format(**addr))
    

def get_posts(sources: dict, targetChannel: str, user = False):
    reddits =  source(sources)
    newtime = {}

    for reddit in reddits:
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
                prepare(post, targetChannel)
                reddit['lastpost'] = max(
                    map(lambda x:x['data']['created'],post)
                )

        newtime[reddit['name']] = reddit['lastpost']
        save_settings(sys.argv[1], newtime)
    return newtime

def send_posts(debug = False):
    src = read_settings(argv[1])
    if debug:
        times = get_posts(src['src'], debugch)
    else:
        times = get_posts(src['src'], src['channel'])
    #save_settings(sys.argv[1], times)

if __name__ == '__main__':
    argv.append(input('enter settings filename: '))
    send_posts(True)