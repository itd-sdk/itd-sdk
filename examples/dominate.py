from time import sleep
from itd import ITDClient
from itd.exceptions import NotFoundError

c = ITDClient(cookies=input('token: '))

cursor = None
while True:
    posts, pagination = c.get_posts(cursor)
    cursor = pagination.next_cursor
    for post in posts:
        if not post.is_liked and post.likes_count == 0:
            try:
                post = c.get_post(post.id)
            except NotFoundError:
                continue
            if post.likes_count == 0: # re-check likes count
                c.like_post(post.id)
            sleep(2)
    sleep(5)


# первым аргументом сразу реверш токен, без "refresh_token="
# c = ITDClient('a152c8eec3fe355goidaaf5802bb2hahahabb3a8zovsvosvoz654ccbcd3219848d4912dec1')
# c.set_action_delay(10) # установить задержку между действиями  # по умолчанию рекоммендованная задержка

# # автопагинация постов
# for post in c.stream_posts(delay=1):
#     post.like() # классы с методами

# user = User('03442f74-a407-40ec-9723-f9b5bb2cca2e') # возможность писать UUID как str
# user.follow()

# for post in user.stream_posts(tab='like'): # возможность писать enum как str
#     post.add_comment('ахахаха')

#     post.comments # список загруженных сейчас
#     post.comments.load(10) # догрузить 10
#     post.comments.get(15) # догрузить 15 + вернуть все
#     post.comments.load_all() # догрузить все
#     post.comments.refresh() # перезагрузить все
#     post.comments.refresh(10) # удалить все и загрузить заново 10 последних

#     post.report('abuse')
