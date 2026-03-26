from itd import ITDClient
# from itd.post import Post
from time import sleep
from random import randint
from dotenv import load_dotenv
from os import getenv

load_dotenv()

c = ITDClient(getenv('TOKEN'))

with open('1.gif', 'rb') as f:
    file_data = f.read()

# file_data += b'\xbb\xff\x3b'
# print(file_data)
agreed = False
file = None
length = len(file_data)
while not agreed:
    rnd = randint(length - length // 90, length)
    file = c.upload_file('some.png', file_data.replace(file_data[rnd:rnd + 3], b'\xff\x00\xb0\x00'))
    if file.mime_type == 'image/jpeg':
        print('not converted to GIF! Try again...')
        sleep(3)
        continue

    print('check this out: ', file.url)
    agreed = input('? ') == 'y'

c.create_post(attachmnet_ids=[file.id])
# Post.new(attachment_ids=[file.id])
