import requests, os, time
from dotenv import load_dotenv
from tinydb import TinyDB
from datetime import datetime

load_dotenv()

token = os.environ['DISCORD_API_TOKEN']

headers = {
    "Authorization": f"Bot {token}",
    "User-Agent": "Telescope",
    "Content-Type": "application/json"
}

db = TinyDB('data.json', indent=4)
messages = db.table("messages")

for m in messages:
    channel_id = m['original_cid']
    message_id = m['original_mid']

    url = f"https://discord.com/api/channels/{channel_id}/messages/{message_id}"


    while True:
        r = requests.get(url, headers=headers)
        data = r.json()

        if (r.status_code == 429):
            timeout = data['retry_after']
            print(f"Being rate limited, waiting {timeout / 1000} seconds")
            time.sleep(timeout / 1000)
            continue

        elif (r.status_code == 200):
            created_at = datetime.fromisoformat(data['timestamp']).replace(tzinfo=None).isoformat()
            edited_at  = datetime.fromisoformat(data['edited_timestamp']).replace(tzinfo=None).isoformat() if data['edited_timestamp'] else None

            messages.update(
                {
                    'created_at': created_at,
                    'edited_at':  edited_at
                },
                doc_ids=[m.doc_id]
            )
            
            print(f"{channel_id} {message_id} -> {created_at}, {edited_at}")
            break

    





