# :material-bell: Notification

!!! note
    В билиотеке есть пока еще нерабочие типы уведомлений, такие как `follow_request`, `mention` и др. Все эти типы взяты из [декомпилированного фронтенда](https://github.com/itd-sdk/itd-frontend), то есть на оф. клиенте они также работают. Ождиается только появление на бэкенде.

## Аттрибуты

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID уведомления.

#### type <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[NotificationType](enums.md#notificationtype)</span></span>
Тип уведомления (например лайк подписка и тд).

#### target_type <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[NotificationTargetType](enums.md#notificationtargettype)</span></span>
Тип цели (например пост). `None`, если цель - пользователь (например при подписках).

#### target_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID цели. `None`, если цель - пользователь (например при подписках).

#### preview <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Описание уведолмения.

 - У лайков и репостов содержание поста.
 - У комментариев и ответов содержание комментария.
 - У подписок и заявок `None`.

#### is_read <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Прочитано ли уведомление.

#### read_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата прочетния уведомления. `None`, если `is_read` == `False`.

#### created_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата создания уведомления.

#### actor <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-user:</span><span class="mdx-badge__text">[User](users.md#user)</span></span>
Актор.

!!! note "glossary"
    Актор (англ. actor) - "создатель" уведомления - комментатор, репостер, подписчик и тд.

#### sound <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли воспроизвести уведомление со звуком. Работает только при стриме уведомлений. Вычисляется на основе настроек уведомлений пользователя.

#### subject_type <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[NotificationSubjectType](enums.md#notificationsubjecttype)</span></span>
Тип объекта, о котором уведомление (сам комментарий или пост), в отличие от [target_type](#target_type-notificationtargettype) - того, к чему этот объект относится. `None`, если объекта нет (например при подписке).

#### subject_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID этого объекта. `None`, если объекта нет.


## :material-eye: Прочитать
```py
notification.read()
```

### Ошибки
 - `NotFoundError` - уведомление не найдено, уже прочитано или не принадлежит клиенту.

## Получить текст
```py
notification.get_text(
    avatar=False
)
```
Получить текст уведомления (вида `fdg оценил(а) ваш комментарий`) (не API метод, сделано для удобства, создается на основе `type`).

### Параметры
#### avatar <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли добавлять аватар актора. По умолчанию `False`.

## Получить цвет
```py
color = notification.get_color()
```
Получить цвет уведомления (`blue`, `green`, `red` или `purple`) (не API метод, сделано для удобства, создается на основе `type`).

---

# :material-code-brackets: :material-bell: Уведомления

 - [x] has_more
 - [ ] total

## Аттрибуты
### unread_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество непрочитанных уведомлений. Запрашивается один раз, дальше само пересчитывается - уменьшается при [прочтении](#_1) и увеличивается при новых уведомлениях из стрима.

## Получить
```py
notifications = Notifications()
```

## :material-email-open: Прочитать все
```py
notifications.read_all()
```

## Стрим уведолмений
```py
for notification in notifications.stream():
    pass
```

## Стрим уведомлений в фоне
```py
thread = notifications.stream_bg(
    daemon=True
)
```

### Параметры
#### daemon <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Влючен ли `daemon` для thread'а.

Чтобы получать уведомления из фона, установите каллбэки.

## Остановка фонового стрима
```py
notifications.stop_stream()
```

## Каллбэки

### Общий
=== "Через декоратор"
    ```py
    @notifications.on()
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_notification = lambda notification: notification.read()
    ```

### Лайки (на постах)
=== "Через декоратор"
    ```py
    from itd.enums import NotificationType

    @notifications.on(NotificationType.LIKE)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_like = lambda notification: notification.read()
    ```

### Комментарии
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.COMMENT)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_comment = lambda notification: notification.read()
    ```

### Ответы
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.REPLY)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_reply = lambda notification: notification.read()
    ```

### Репосты
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.REPOST)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_repost = lambda notification: notification.read()
    ```

### Упоминания (в постах)
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.MENTION)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_mention = lambda notification: notification.read()
    ```

### Подписчики
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.FOLLOW)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_follow = lambda notification: notification.read()
    ```

### Запросы на подписку
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.FOLLOW_REQUEST)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_follow_request = lambda notification: notification.read()
    ```

### Принятие запросов на подписку
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.FOLLOW_ACCEPTED)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_follow_accepted = lambda notification: notification.read()
    ```

### Лайки комментариев
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.COMMENT_LIKE)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_comment_like = lambda notification: notification.read()
    ```

### Упоминания (в комментариях)
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.COMMENT_MENTION)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_comment_mention = lambda notification: notification.read()
    ```
### Посты на стене
=== "Через декоратор"
    ```py
    @notifications.on(NotificationType.WALL_POST)
    def callback(notification: Notification):
        notification.read()
    ```
=== "Через переопределение"
    ```py
    notifications.on_wall_post = lambda notification: notification.read()
    ```

---

# :material-cog: NotificationsSettings
Настройки уведомлений.

## Получить
```py
settings = NotificationsSettings()
```

## Аттрибуты
#### enabled <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Включены ли уведомления .

#### web_enabled <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Включены ли уведомления в браузере (пока точно непонятно что это значит).

#### sound <span class="mdx-badge"><span class="mdx-badge__icon">:material-volume-high:</span><span class="mdx-badge__text">bool</span></span>
Проигрывать ли звук. Именно на основе этой настройки у [уведомления](#notification) проставляется [sound](#sound-bool).

#### follows <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Уведомлять о новых подписчиках.

#### likes <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Уведомлять о лайках.

#### comments <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Уведомлять о комментариях.

#### replies <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Уведомлять об ответах на комментарии.

#### mentions <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Уведомлять об упоминаниях.

#### wall_posts <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Уведомлять о постах на вашей стене.

## :material-pencil: Обновить
```py
settings.update(likes=False, mentions=False)
```

### Параметры
#### old <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Отправлять ли настройки в старом формате. По умолчанию `True`.

#### new <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Отправлять ли настройки в новом формате. По умолчанию `True`.

!!! note
    ИТД пока принимает оба формата, поэтому SDK по умолчанию шлет сразу оба - так настройки применятся и на старом, и на новом бэкенде.


## :material-pencil: Обновить из аттрибутов

```py
settings.likes = False
settings.update_from_fields()
```
