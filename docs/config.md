# Конфигурация

У `ITDClient` можно настраивать конфигурацию:

```python
from itd import ITDClient, ITDConfig

config = ITDConfig()

ITDClient('xxx', config=config)
```

## Параметры

#### rate_limit <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">RateLimitMode</span></span>
Устанавливает дефолтные значения задержек.  
Обычные запросы - запросы без конкретно утсановленных задержек (например получение постов, подписчиков, удаление поста и тд). У каждого менее обычного запроса (подписка, лайк, комментарий и тд) стоят уже свои задержки (например, при создании поста задержка 5-30 сек взависимости от режима).

 - `RateLmitMode.NO`: 0 сек - для простых скриптов
 - `RateLimitMode.MIN`: Небольшие задержки (0 сек для обычных запросов) - для кастомных клиентов или маленьких скриптов
 - `RateLimitMode.MID`: Средние задержки (0.2 сек для обычных запросов) - для обычных скриптов
 - `RateLimitMode.MAX`: Большие задержки (0.4 сек для обычных запросов) - для больших ботов, парсеров

##### Псевдокод: как работает rate_limit_mode внутри
```python
if функция есть в предустановленных значениях: # (1)
    задержка = предустановленное значение
elif rate_limit_mode == RateLimitMode.NO:
    задержка = 0
elif any((кастомная_задержка_min, кастомная_задержка_mid, кастомная_задержка_max)):
    задержка = eval(f'задержка_{min or mid or max}')
else:
    задержка = задержка_для_обычных_запросов # (2)
```

1. (см. [rate_limit_actions](#rate_limit_actions-dictstr-float))
2. (см. [rate_limit_default](#rate_limit_default-float))

<!-- Также планируется режим `SMART`, который будет выставлять динамическую задержку (например при первых трех комментариях не делать задержку). -->

#### rate_limit_default <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Задержка для обычных запросов (overrides rate_limit_mode).

#### rate_limit_actions <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-braces: :material-text:: :octicons-number-16:</span><span class="mdx-badge__text">dict[str, float]</span></span>
Кастомная задержка для каждого вида запроса (например `get_user`). Названия фукнций можно посмотреть в `itd.api`. Можно использовать, если ваш скрипт повторяет одно и тоже действие (например, постоянно комментирует).

!!! example
    ```python
    {'get_me': 5, 'get_followers: 6, 'add_comment': 5.4}
    ```

#### is_default <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Сделать ли клиент дефолтным по умолчанию. По умолчанию дефолтным становится первый инициализированный клиент.

#### userposts_add_pinned_post <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Добавлять ли закрепленный пост при получении постов пользователя (`UserPosts`). Для этого потребуется отдельный запрос.

#### auto_load <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли автоматически загружать данные при попытке получение (перехват в `__getattribute__`). Если выключено, то для получения данных придется перед получением писать `obj.refresh()`.

#### load_on_getitem <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли подгружать данные при попытке получить еще не загруженный элемент списка (например `Posts()[10]`). Может выдать `AttributeError`, если даже после загрузки всех объектов количество меньше желаемого индекса, или если известно общее количество объектов и индекс будет больше него.

#### load_on_getitem_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int | All</span></span>
Количество доп. загружаемых объектов при попытке получить еще не загруженный элемент списка. По умолчанию 1. `All` - загрузить все.

!!! example
    ```python
    config.load_on_getitem_count = 1
    posts[5]
    len(posts) # 6

    config.load_on_getitem_count = 5
    posts[6]
    len(posts) # 12

    config.load_on_getitem_count = ALL
    posts[7]
    len(posts) # 50

    config.load_on_getitem_count = 0
    posts[8] # AttributeError
    ```

#### force_load_lists <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Загружать список, даже если `has_more = False`. Может уйти в бесконечный цикл при итерации.

#### debug_response <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">DebugResponseMode</span></span>
Режим показа сырых данных ответа API (response). Для работы должен быть установлен логгер с режимом `DEBUG`.
 - `DebugResponseMode.NO`: Не показывать ответ.
 - `DebugResponseMode.BEFORE`: Показывать ответ до обработки (сырой).
 - `DebugResponseMode.AFTER`: Показывать ответ после обработки (если при обработке возникла ошибка, ответ не выведется).
 - `DebugResponseMode.KEYS`: Показывать только ключи ответа (после обработки).


#### timeout <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Таймаут обычного запроса.

#### timeout_file <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Таймаут при загрузке файла.

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Базовый URL ИТД (`xn--d1ah4a.com`).

#### url_api <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
URL к API ИТД (`https://xn--d1ah4a.com/api`). Если не указан, берется из [url](#url-str).

#### user_agent <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
User-Agent, под которым обращатся к API ИТД. Если вы делаете свой клиент, можете поставить агент как его имя.

#### solve_challenge <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли проходить JS-challenge (защита от скриптов). Иногда включается при запросах к API. Если выключена, скрипт может упасть с ошибкой `fail to parse json`.
