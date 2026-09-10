# Рейт лимиты
У ИТД есть 4 вида рейт лимитов:

## Для каждого эндпоинта
У каждого эндпоинта есть свой лимит запросов в минуту (можно посмотреть в заголовке `x-ratelimit-limit`). Оставшееся количество запросов можно посмотреть в заголовке `x-ratelimit-remaining`. У запросов с одним лимитом общее оставшееся количество запросов. При достижении лимита в ответе будет `{'error': 'Too Many Requests'}`. Лимит распространяется на все запросы с одного IP. У каждого лимита своя скорость заполнения.

!!! note "glossary"
    Токен - стоимость одного запроса. При новом запросе сниамется 1 токен.

### Пример:
```py
 - get_hashtags -> limit=13 remaining=12
 - get_hashtags -> limit=13 remaining=11
 - get_hashtags -> limit=13 remaining=10
...
 - get_hashtags -> limit=13 remaining=0
 - get_hashtags -> rate limit # (1)
```

1. После исчерпания `x-ratelimit-remaining` в следующем запросе будет `{'error': 'Too Many Requests'}`.

```py
 - get_users -> limit=40 remaining=39
 - get_following -> limit=40 remaining=38  # (1)
 - get_followers -> limit=40 remaining=37
 - get_users -> limit=40 remaining=36
 ...
 - get_users -> limit=40 remaining=1
 - get_blocked -> limit=40 remaining=0
 - get_followers -> rate limit 
 - get_posts -> limit=150 remaining=149  # (2)
```

1. с одинаковым `x-ratelimit-limit` общий `x-ratelimit-remaining`
2. лимит действует только на запросы с таким же `x-ratelimit-limit`

## Для действий (минутный и часовой)
У каждого действия (лайк, подписка, комментарий итд) а также поиска есть отдельные лимиты (отличатся от первого, хотя они тоже на них есть) запросов в минуту и в час. При достиежении лимита в ответе будет `{'error': {'code': 'RATE_LIMIT_EXCEEDED', 'retry_after': 59, 'message': 'Слишком много лайков. Повторите позже.'}}`. `retry_after` вычисляется из даты первого запроса за последние `60 сек` (`60 мин` если лимит часовой) минус дата последнего запроса. Лимит распространяется на все запросы с одного аккаунта.

| Действие                        | В минуту | В час |
|---------------------------------|----------|-------|
| Лайки                           | 30       | 200   |
| Создание комментариев и ответов | 5        | 75    |
| Подписки                        | 5        | 20    | 
| Репосты                         | 5        | 25    |
| Создание постов                 | 5        | 25    |

<a id="ip"></a>
## По IP
Если сделать более 100 запросов за минуту (примерное значение, в реальности может быть другое), ИТД будет недоступен с вашего IP на несколько часов (как будто он не работает). В SDK стоит лимит `90запросов\сек`, после которого идет задержка на `60 сек`. Отключается через `set_limiter_config(ip_limiter=None)` (см. [ip_limiter](#ip_limiter-ipratelimiter)).

---

## Защита
В SDK есть встроенная защита от рейт лимитов. Насторить можно через `set_limiter_config`:
```py
from itd import HalfRateLimiter, set_limiter_config

set_limiter_config(
    limiter=None,
    ip_limiter=None,
    auto_acquire=False
)
```

### Параметры
#### limiter <span class="mdx-badge"><span class="mdx-badge__icon">:simple-speedtest:</span><span class="mdx-badge__text">type[RateLimiter]</span></span>
Лимитер на эндпоинты с одним лимитом (на все запросы с лимитом `40` будет один лимитер, на `60` - другой). Текущий лимит лимитера есть в `self.capacity`. `None` - убрать лимитер.
```py
set_limiter_config(limiter=HalfRateLimiter)
```

Есть 2 встроенных лимитера:

##### HalfRateLimiter
Оставляет примерно половину `remaining`, угадывает задрежку: 
```py
from itd import HalfRateLimiter, set_limiter_config

set_limiter_config(limiter=HalfRateLimiter)
```

##### BurstRateLimiter
Всаживает весь `remaining` без задержек с перерывом 60сек между залпами:
```py
from itd import BurstRateLimiter, set_limiter_config

set_limiter_config(limiter=BurstRateLimiter)
```

##### Кастом
Также можно создать свой лимитер, для этого можно унаследоваться от абстракатного класса `RateLimiter`.

```py
from itd import RateLimiter, set_limiter_config

class TestRateLimiter(RateLimiter):
    def sync(self, remaining: int):
        """
        вызывается после запроса
        здесь должна быть логика обновления задержки
        "remaining" в параметрах - новое количество оставшихся запросов, из которых нужно вычилсить новую задержку
        """
        self._delay = (self.capacity - remaining) / 10 # пример формулы

    def on_limit(self):
        """
        вызывается при рейт лимите после запроса
        """
        self._delay *= 2

set_limiter_config(limiter=TestRateLimiter)
```

#### ip_limiter <span class="mdx-badge"><span class="mdx-badge__icon">:simple-speedtest:</span><span class="mdx-badge__text">IPRateLimiter</span></span>
Лимитер на все эндпоинты. `None` - убрать лимитер.
```py
set_limiter_config(limiter=IPRateLimiter())
```

#### auto_acquire <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли автоматически ждать задержку лимитера, нужен для оптимизации. По умолчанию `True`.

Если выключен, ждать нужно самому через `acquire_limiters()`. Функция выбирает самую длинную задержку и ждет только ее.

=== "Без auto_acquire"
    ```py
    from itd import acquire_limiters, set_limiter_config, HalfRateLimiter
    set_limiter_config(limiter=HalfRateLimiter, auto_acquire=False)

    while True:
        User('itd_sdk').followers # +8 cек
        Posts().load(2) # +1 сек
        Hashtags() # +10 сек
        Me().refresh() # +8 сек
        acquire_limiters() # ждет только самую длинную задержку, т.е 10
        # итого 10сек
    ```

=== "С auto_acquire"
    ```py
    from itd import set_limiter_config, HalfRateLimiter
    set_limiter_config(limiter=HalfRateLimiter, auto_acquire=True)

    while True:
        User('itd_sdk').followers # +8 cек
        Posts().load(2) # +1 сек
        Hashtags() # +10 сек
        Me().refresh() # +8 сек
        # итого ~27сек
    ```
