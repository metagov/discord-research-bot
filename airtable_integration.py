from exported import messages
from comments import comments
from airtable import Airtable
import time
import json

table = Airtable(
    # ...
    # ...
    # ...
)

def retrieve_comments(m_id):
    to_return = {}
    for c in comments:
        if c['original_mid'] == m_id:
            author = c['author']['name']
            content = c['content']

            to_return[author] = content
    
    return to_return

for m in messages:
    if 'content' in m:
        d = {
            'id'        : str(m['original_mid']),
            'content'   : m['content'],
            'created_at': m['created_at'],
            'edited_at' : m['edited_at'],
            'attachment_urls': None,
            'deleted': False,
            'channel_id': str(m['channel']['id']),
            'channel_name': m['channel']['name'],
            'guild_id': str(m['guild']['id']),
            'guild_name': m['guild']['name'],
            'curated_by': m['metadata']['curated_by']['name'],
            'curated_at': m['metadata']['curated_at'],
            'requested_by': m['metadata']['requested_by']['name'],
            'requested_at': m['metadata']['requested_at'],
            'fulfilled_at': m['metadata']['fulfilled_at'],
        }

        if 'author' in m:
            d.update({
                'author_is_anonymous'   : False,
                'author_hash'           : m['author_hash'],
                'author_id'             : str(m['author']['id']),
                'author_name'           : m['author']['name'],
                'author_discriminator'  : m['author']['discriminator'],
                'author_nick'           : None,
            })
        else:
            d.update({
                'author_is_anonymous'   : True,
                'author_hash'           : m['author_hash'],
                'author_id'             : None,
                'author_name'           : None,
                'author_discriminator'  : None,
                'author_nick'           : None,
            })
        
        message_comments = retrieve_comments(m['original_mid'])
        comment_string = json.dumps(message_comments)

        d['researcher_comments'] = None if comment_string == '{}' else comment_string

        print(table.insert(d))
        time.sleep(0.2)
