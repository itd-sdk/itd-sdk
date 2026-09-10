# Migration Guide

## 2.7.1 -> 2.8.0

### Пакет разделен на слои
`itd/core` (клиент, конфиг, запросы, базовая моделька), `itd/api` (эндпоинты) и `itd/models` (модели). Если вы импортируете из самого `itd`, ничего не меняется:

```py
from itd import ITDClient, Post, User, Notifications  # работает как раньше
```

Изменились только прямые импорты внутренних модулей:

=== "2.7.1"

    ```py
    from itd.post import Post
    from itd.client import Config
    from itd.logger import setup_logging
    ```

=== "2.8.0"

    ```py
    from itd.models.post import Post
    from itd.core.config import Config
    from itd.core.logger import setup_logging
    ```

`itd.enums` и `itd.exceptions` остались на месте.

### Методы поиска убраны из клиента

=== "2.7.1"

    ```py
    users, hashtags = client.search('итд')
    users = client.search_users('итд')
    is_following = client.get_follow_status(user_id)
    ```

=== "2.8.0"

    ```py
    from itd import Users, Hashtags, get_follow_status

    users = Users.search('итд')
    hashtags = Hashtags.search('итд')
    is_following = get_follow_status(user_id)
    ```

### is_token_expired стал property

=== "2.7.1"

    ```py
    client.is_token_expired()
    ```

=== "2.8.0"

    ```py
    client.is_token_expired
    ```

### Видимые посты перенесны в трекер
`client.visible_posts`, `client.set_active()` и `client.update_post_stats()` работают как раньше, но само состояние и таймеры теперь в `client.visibility` - их можно останавливать (`client.visibility.stop()`).

### Удалено устаревшее
 - `base.rate_limit` - вместо него `set_limiter_config` (см. [рейт лимиты](limits.md#_5))
 - `config.load_comments_from_post` - вместо него `post.first_comments` и `post.comments`
 - `config.rate_limit`, `rate_limit_default`, `rate_limit_actions`, `anti_rate_limit`, `burst_requests`, `anti_ip_ban`, `limit_coefficient`, `auto_acquire` - все настройки задержек переехали в `set_limiter_config`

## 2.3.0 -> 2.4.4
!!! warning
    В версиях 2.4.0 - 2.4.3 есть критические ошибки. Используйте 2.4.4.

 - ITDlist.load возвращает только новые объекты

=== "2.3.0"

    ```py
    posts = Posts()
    posts.load(5)
    print(len(posts.load(5))) # 10
    ```

=== "2.4.4+"

    ```py
    posts = Posts()
    posts.load(5)
    print(len(posts.load(5))) # 5
    ```

 - Удалены `config`.{`rate_limit_wait`,`retry_on_rate_limits`} (устарели в 2.2.0)

=== "2.1.2"

    ```py
    config = ITDConfig(
        rate_limit_wait=1,
        retry_on_rate_limits=True
    )
    ```

=== "2.4.4+ (2.2.0+)"

    ```py
    config = ITDConfig(
        retry_delay=1,
        retry_enabled=True
    )
    ```

## 1.8.3 -> 2.0.0

 - Удален `cookies`, переименован `access_token` => `access`, добавлен `refresh` в `ITDClient.__init__`

=== "1.8.3"

    ```py
    c = ITDClient(
        cookies='refresh_token=xxx',
        access_token='eyXXX'
    )
    ```

=== "2.0.0+"

    ```py
    c = ITDClient(
        refresh='xxx',
        access='eyXXX'
    )
    ```

 - Добавлено окончание `Error` ко всем ошибкам

=== "1.8.3"

    ```py
    from itd.exceptions import NotFound, Forbidden, CantRepostYourself
    ```

=== "2.0.0+"

    ```py
    from itd.exceptions import NotFoundError, ForbiddenError, CantRepostYourselfError
    ```

 - Переименован `is_blocked` и `is_followed` в `User`

=== "1.8.3"

    ```py
    print(user.is_blocked, user.is_followed)
    ```

=== "2.0.0+"

    ```py
    print(user.is_blocked_by, user.is_followed_by)
    ```

 - Переименован модуль с роутами (`routes`)

=== "1.8.3"

    ```py
    from itd.routes.users import get_user
    ```

=== "2.0.0"

    ```py
    from itd.api.users import get_user
    ```

 - Удалено большинство функций из `ITDClient`, удален модуль с моделями (`models`)

=== "1.8.3"

    ```py
    c = ITDClient('xxx')
    c.get_me()
    c.create_post('test')
    c.follow('fdg')
    # и так далее по смыслу
    ```

=== "2.0.0+"

    ```py
    from itd import Me, Post, User

    ITDClient('xxx')
    Me()
    Post.new('test')
    User('fdg').follow()
    # и так далее по смыслу
    ```

 - Переименован параметр `attachment_ids` при создании комментария или поста

=== "1.8.3"

    ```py
    c.create_post(attachment_ids=['69cb7f5e-1ca8-486f-b883-89436c308df5'])
    c.add_comment(
        '1e02ff60-f1fb-48c9-b304-f2c536d2c944',
        attachment_ids=['69cb7f5e-1ca8-486f-b883-89436c308df5']
    )
    ```

=== "2.0.0+"

    ```py
    Post.new(
        attachments='69cb7f5e-1ca8-486f-b883-89436c308df5' # также может быть объектом файла, списком или UUID
    )
    Post('1e02ff60-f1fb-48c9-b304-f2c536d2c944').comments.new(
        attachments=['69cb7f5e-1ca8-486f-b883-89436c308df5']
    )
    ```
