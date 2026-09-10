# :fontawesome-solid-gear: Конфигурация

У `ITDClient` можно настраивать конфигурацию:

```python
from itd import ITDClient, ITDConfig

config = ITDConfig()

ITDClient('xxx', config=config)
```

## Общее

#### client_type <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Тип клиента. По умолчанию `onetime`.

 - `onetime`: Одноразовый скрипт
 - `client`: Реальный клиент
 - `bot`: Бот

От него зависят значения по умолчанию: [timeout](#timeout-float), [retry_enabled](#retry_enabled-bool), [retry_exceptions](#retry_exceptions-tupletypeexception), [post_update_stats](#post_update_stats-bool) и [dwell_check_active](#dwell_check_active-bool).

!!! question "Почему не enum?"
    ~~Лень было.~~ Чтобы было меньше импортов. Я вообще хочу постепенно отказать от enum в пользу `Literal`, как это сделали [textual](https://textualize.io) например.

#### is_default <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Сделать ли клиент дефолтным по умолчанию. По умолчанию дефолтным становится первый инициализированный клиент.

#### userposts_add_pinned_post <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Добавлять ли закрепленный пост при получении постов пользователя (`UserPosts`). Для этого потребуется отдельный запрос. По умолчанию `True`.

## Загрузка данных

#### load_on_init <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Загружать ли модель сразу при создании (`Post('...')` тут же сходит в API). По умолчанию `False` - модель загрузится, когда у нее что-нибудь спросят.

#### load_on_getattr <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли автоматически загружать данные при попытке получения (перехват в `__getattribute__`, см. [авто-загрузку](features.md#_1)). Если выключено, то перед получением придется писать `obj.refresh()`. По умолчанию `True`.

Узнать, загружено ли поле, не вызывая догрузку, можно через [is_loaded](ref/base.md):

```python
post.is_loaded('content')
```

#### load_on_getitem <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16: | ALL | BATCH</span><span class="mdx-badge__text">int | All | Batch</span></span>
Количество загружаемых объектов при попытке получить еще не загруженный элемент списка (например `Posts()[10]`). Может выдать `AttributeError`, если даже после загрузки всех объектов количество меньше желаемого индекса, или если известно общее количество объектов и индекс будет больше него. По умолчанию `1`. `All` - загрузить все. `Batch` - загрузить следующий батч (следующий по курсору). `None` - выключить авто загрузку.

!!! example
    ```python
    config.load_on_getitem = 1
    posts[5]
    len(posts) # 6

    config.load_on_getitem = 5
    posts[6]
    len(posts) # 12

    config.load_on_getitem = ALL
    posts[7]
    len(posts) # 50

    posts.clear()
    config.load_on_getitem = None
    posts[8] # AttributeError
    ```

#### load_on_iter <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16: | ALL | BATCH</span><span class="mdx-badge__text">int | All | Batch</span></span>
Количество загружаемых объектов при итерации списка (например `for post in Posts()`) Если вы итеририуете сразу весь список без `break`, то этот пратаметр особо не играет роли. По умолчанию `BATCH`. `All` - загружать все. `Batch` - загружать следующий батч. `None` - выключить авто загрузку.

#### force_load_lists <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Загружать список, даже если `has_more = False`. Может уйти в бесконечный цикл при итерации. По умолчанию `False`.

#### batch_sizes <span class="mdx-badge"><span class="mdx-badge__icon">:material-tune:</span><span class="mdx-badge__text">BatchSizes</span></span>
Сколько объектов запрашивать за раз у каждого списка.

```python
from itd import ITDConfig
from itd.core.config import BatchSizes

config = ITDConfig(batch_sizes=BatchSizes(preset='max', comments=100))
```

Пресет задается через `preset` (`decreased`, `default`, `increased`, `max`), а также любой список можно переопределить отдельно вручную (`comments`, `replies`, `hashtags`, `notifications`, `posts`, `user_posts`, `liked_posts`, `hashtag_posts`, `followers`, `following`, `blocked`).

| список                                        | decreased | default | increased | max  |
| --------------------------------------------- | --------- | ------- | --------- | ---- |
| comments                                      | 50        | 100     | 200       | 500  |
| replies                                       | 20        | 100     | 100       | 100  |
| hashtags                                      | 5         | 10      | 20        | 50   |
| notifications                                 | 10        | 20      | 50        | 1000 |
| posts, user_posts, liked_posts, hashtag_posts | 10        | 20      | 30        | 50   |
| followers, following, blocked                 | 10        | 20      | 50        | 100  |

!!! info
    У уведомлений неограниченный лимит. В `max` пресете он задан в `1000`.

## Запросы

#### debug_response <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[DebugResponseMode](ref/enums.md#debugresponsemode)</span></span>
Режим показа сырых данных ответа API (response). Для работы должен быть установлен логгер с режимом `DEBUG`.

!!! warning
    Может раскрыть ваши ключи (при `refresh_auth` в терминале будет виден `access_token`)
По умолчанию `DebugResponseMode.NO`.

#### timeout <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Таймаут обычного запроса. По умолчанию зависит от [client_type](#client_type-str): `5` для `onetime`, `20` для `client` и `60` для `bot`.

#### timeout_file <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Таймаут при загрузке файла.

#### timeout_file_download <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Таймаут при скачивании файла или вложения ([download](ref/files.md)).

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
URL к API ИТД. По умолчанию `https://xn--d1ah4a.com/api`.

#### user_agent <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str | [UserAgent](ref/enums.md#useragent)</span></span>
User-Agent, под которым обращатся к API ИТД. Если вы делаете свой клиент, можете поставить агент как его имя. По умолчанию стоит дефолтный браузерный user-agent.

#### solve_challenge <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли проходить JS-challenge (защита от скриптов). Иногда включается при запросах к API. Если выключена, скрипт может упасть с ошибкой `fail to parse json`.

#### parse_mode <span class="mdx-badge"><span class="mdx-badge__icon">:simple-markdown:</span><span class="mdx-badge__text">[ParseMode](ref/enums.md#parsemode)</span></span>
Режим парсинга (автоматически генерирует `spans` при создании или редактировании постов). По умолчанию `ParseMode.NO`.

#### token_expiry_margin <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
За сколько секунд до истечения access токен считается протухшим. Запас нужен, чтобы токен не истек, пока запрос идет по сети, и на случай, если часы на машине немного расходятся с серверными. По умолчанию `60`.

#### refresh_token_cookie_name <span class="mdx-badge"><span class="mdx-badge__icon">:material-cookie:</span><span class="mdx-badge__text">str</span></span>
Имя куки, в которой лежит refresh токен. По умолчанию `refresh_token`.

## Повторы запросов

#### retry_enabled <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли повторять запрос при ошибке сети или рейт лимите. По умолчанию `True` для ботов, `False` для остальных.

#### retry_delay <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Задержка перед следующим повтором запроса, если ИТД не прислал свою (`retryAfter`). По умолчанию `10`.

#### retry_max_retry_after <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Максимальное время ожидания, которое SDK готов принять от ИТД. Если рейт лимит просит ждать дольше - ошибка выбрасывается, а не проглатывается. По умолчанию `500`.

#### retry_max_retries <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Максимальное количество попыток повтора запроса. `None` - без лимита. По умолчанию `10`.

#### retry_exceptions <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-close-circle:</span><span class="mdx-badge__text">tuple[type[Exception], ...]</span></span>
Список ошибок, при которых нужно повторить запрос. По умолчанию для ботов - `RateLimitError` и стандартные ошибки из `requests` (`RequestException`), для остальных повторов нет.

#### on_exceptions <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-braces: :material-close-circle:: :material-function:</span><span class="mdx-badge__text">dict[type[Exception], Callable]</span></span>
Колбэки на ошибки: вызываются перед тем, как ошибка будет выброшена. Удобно, чтобы, например, слать их в телеграм.

!!! example
    ```python
    config.on_exceptions = {RateLimitError: lambda e: print('поймали лимит', e.retry_after)}
    ```

Колбэк подберется и для наследников - если указать `ITDException`, будут ловиться все ошибки SDK.

## Авторизация

#### bypass_auth_level <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Bypass пре-валидации на проверку уровня авторизации. По умолчанию `False`.
!!! note
    В sdk существует 3 уровня авторизации:

     - `NO`: **Без авторизации** - доступен поиск
     - `ACCESS`: **Access-токен** - доступно большинство всех возможностей
     - `REFRESH`: **Refresh-token** - то же, что и `ACCESS` + обновление токена и выход

    Если вы попытаетесь выполнить запрос который выше по масти, будет вызвана ошибка `InsufficientAuthLevelError`.  
    Чтобы этой ошибки не было, нужно поставить `bypass_auth_level=True`. Тогда будет вызвана стандартная ошибка от самого ИТД (`RefreshTokenMissingError` / `UnauthorizedError` или похожие)

!!! warning
    При вызове ошибок `RefreshTokenMissingError` и `UnauthorizedError` может попросить оставить Issue на github. Если у вас включен `bypass_auth_level`, игнорируйте эту просьбу.

## Просмотры (dwell)

#### dwell_enabled <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли включать dwell tracker для просмотров. По умолчанию `True`.

#### dwell_max_buffer <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Максимальный буффер dwell tracker`а. После переполнения буффер автоматически отпарвится на сервер и очистится. По умолчанию 20 (в точности как у оф клиента).

#### dwell_send_interval <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Задержка между запросами dwell tracker'а (через сколько секунд повторять проверку на наличие новых записей, и если есть то отправлять их на сервер). По умолчанию 2 (в точности как у оф клиента). `0` - не запускать таймер вообще.

#### dwell_save_on_quit <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Отправлять ли несохраненные записи перед закрытием скрипта (делается через atexit). По умолчанию `True`.

#### dwell_wait_durations <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Ждать ли просмотр по-настоящему: перед отправкой просмотра скрипт поспит столько, сколько по расчетам человек читал бы этот пост ([view_read_speed](#view_read_speed-int) и [view_images_speed](#view_images_speed-int)). По умолчанию `False`.

!!! warning
    Ожидание блокирует поток, из которого вызвали просмотр.

#### dwell_min_duration <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Минимальная длительность просмотра (мс). Если пост увидели быстрее, просмотр не отправится. По умолчанию `250`.

#### dwell_max_duration <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Максимальная длительность просмотра (мс) - больше нее время не рассчитывается. По умолчанию `30000`.

#### dwell_check_active <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Следить ли за активностью: если пользователь ничего не делает, видимые посты скрываются (как будто он ушел со страницы), а когда возвращается - показываются снова. По умолчанию `True` для `client`, `False` для остальных.

Активность отмечается вручную:

```python
client.set_active()  # скролл, движение мыши итд
```

#### dwell_check_active_interval <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Как часто проверять активность (сек). По умолчанию `5`.

#### dwell_inactive_timeout <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Через сколько секунд без активности пользователь считается ушедшим. По умолчанию `30`.

#### post_auto_view <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Отправлять ли просмотр автоматически при `post.set_invisible()`. По умолчанию `True`.

#### post_view_increment <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Увеличивать ли `post.views_count` локально после просмотра. По умолчанию `False`.

#### post_update_stats <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли обновлять статистику видимых постов. По умолчанию `True` для `client`, `False` для остальных.

#### post_update_stats_interval <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Задержка между обнолвением статистики видимых постов. По умолчанию `3`.

#### view_read_speed <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Скорость чтения (в WPM). Используется для более правдоподобного времени просмотра поста. По умолчанию `250`.

#### view_images_speed <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Скорость понимания картинок. Используется для более правдоподобного времени просмотра поста. По умолчанию `130`.

## Рейт лимиты
Задержки между запросами настраиваются через `set_limiter_config` (см. [Рейт лимиты](limits.md#_5)), потому что ITDConfig настраивает конкретного клиента, а лимиты работают на весь сркипт.
