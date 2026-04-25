# itd-sdk
Клиент ITD для python  
Документация (beta): https://firedotguy.github.io/itd-sdk

## Установка

```bash
pip install itd-sdk
```

## Пример

```python
from itd import ITDClient, Me

c = ITDClient('token')
print(Me())
```
<!--
> [!NOTE]
> Берите refresh_token из запроса /auth/refresh. В остальных запросах нету refresh_token
> ![cookie](cookie-screen.png) -->

### Получение cookies

Для получения access_token требуются cookies с `refresh_token`. Как их получить:

1. Откройте [итд.com](https://xn--d1ah4a.com) в браузере
2. Откройте DevTools (F12)
3. Перейдите на вкладку **Network**
4. Обновите страницу
5. Найдите запрос к `/auth/refresh`
6. Скопируйте значение **refresh_token** из **Cookie** из Request Headers

![cookie](cookie-screen.png)


## API
```python
from itd import Me, User, Post, Posts, File, Hashtag, Notifications

me = Me() # получить себя
me.privacy.update(is_private=True)

user = User('itd_sdk') # получить пользователя
user.follow()

post = Post('725681ba-2aaa-42d8-87fb-490c0f44e162') # получить пост
post.like()
post.add_comment('тест комент 6 7')

posts = Posts() # получить посты из ленты
for i, post in enumerate(Posts()):
    post.like() # встроенные защиты, из-за которых рейт-лимит будет получить сложнее + авто ожидание окончания рейт лимита
    if i > 10:
        break

post = user.posts[5] # индексация, авто-получение до нужного значения
post.repost()

file = File.from_path('1.jpg') # загрузка файлов
Post.new('всем привет!', attachments=file) # attachments может быть списком, файлом, или UUID

hashtag = Hashtag('тестапи') # получить данные хэштэга
print(hashtag.posts_count)
hashtag.posts[0].like()

notifications = Notifications() # получить уведы
notifications[30].read()
notifications.read_all()
for notification in notifications.stream(): # SSE уведомлений
    print(notification.type.value)
    break

def on_like(notification):
    print('лайк от', notification.actor.username)
    notifications.stop_stream()
notifications.on_like = on_like
stream = notifications.stream_bg() # background SSE

Post('02bcbba4-f365-4b98-9291-d0bc1fb36fe4').poll.vote('тест') # голосования в опросах

```

### Кастомные запросы

```python
from itd.request import fetch

fetch(c, 'метод', 'эндпоинт', {'данные': 'данные'})
```
Из методов поддерживается `get`, `post`, `put` итд, которые есть в `requests`
К названию эндпоинта добавляется домен итд и `api`, то есть в этом примере отправится `https://xn--d1ah4a.com/api/эндпоинт`.

> [!NOTE]
> `xn--d1ah4a.com` - punycode от "итд.com"

## Прочее
 - Лицезия: [MIT](./LICENSE)
 - Автор:
   - ИТД: [itd_sdk](https://xn--d1ah4a.com/@itd_sdk) или [@fdg](https://xn--d1ah4a.com/@pingbot)
   - ТГ: [@desicars](https://t.me/desicars)

[![Star History Chart](https://api.star-history.com/chart?repos=itd-sdk/itd-sdk&type=date&legend=top-left)](https://www.star-history.com/?repos=itd-sdk%2Fitd-sdk&type=date&legend=top-left)