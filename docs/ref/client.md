# ITDClient

=== "С сохранением"
    ```py
    c = init_client(
        'default',
        initial_refresh=None, 
        verify_refresh=None,
        config=ITDConfig()
    )
    ```
    ### Параметры
    #### name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
    Уникальное имя сессии. Файл с токенами будет сохранен под этим именем. По умолчанию `default`.

    !!! tip
        Используйте разные имена сессий для разных аккаунтов.
    
    #### initial_refresh <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
    Refresh токен. Если не указан, будет взят из env `ITD_REFRESH_TOKEN` или попросится напрямую в консоли (через `input`).

    #### verify_refresh <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
    Нужно ли проверить токен на валидность сразу после инициализации. Полезно для реальных клиентов (сразу покзаать ошибку пользователю при неверном значении). По умолчанию `False`.
    
    #### config <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-gear:</span><span class="mdx-badge__text">ITDConfig</span></span>
    [Конфиг](../config.md).

    !!! note
        `init_client` - это обертка над `ITDClient.from_file` с теми же параметрами.

    Токены лежат в файле сессии - там же SDK хранит и [прочитанные анонсы](announcements.md). Обновленный access токен пишется в файл сам, так что при следующем запуске скрипт не будет обновлять его заново.

=== "Без сохранения"
    ```py
    c = ITDClient(
        refresh='xxx',
        access=None,
        config=ITDConfig()
    )
    ```

    ### Параметры
    #### refresh <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
    Refresh токен.
    
    #### access <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
    Access токен (JWT).
    
    #### config <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-gear:</span><span class="mdx-badge__text">ITDConfig</span></span>
    [Конфиг](../config.md).

## Аттрибуты
#### user <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-user:</span><span class="mdx-badge__text">[Me](users.md#me)</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Пользователь этого клиента (тоже самое, что и `Me()`). Создается один раз при первом обращении.

#### user_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
ID пользователя. Берется из access токена.

#### token <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Access токен.

#### access_token_data <span class="mdx-badge"><span class="mdx-badge__icon">:material-key:</span><span class="mdx-badge__text">AccessToken</span></span>
Раскодированный access токен: `session_id`, `subject_id`, `issued_at`, `expired_at`, `roles`, `is_active`, `issuer` и `jwt_id`.

#### is_token_expired <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Истек ли access токен (с запасом [token_expiry_margin](../config.md#token_expiry_margin-float), чтобы токен не протух прямо во время запроса).

#### can_refresh_auth <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Есть ли refresh токен, то есть сможет ли клиент обновить access токен сам.

#### auth_level <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AuthLevel](enums.md#authlevel)</span></span>
Текущий уровень авторизации, зависит от того, что есть у клиента.

#### visible_posts <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-post:</span><span class="mdx-badge__text">list[[Post](posts.md#post)]</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Посты, видимые прямо сейчас (те, для которых вызвали `post.set_visible()`).

#### last_active <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Когда последний раз отмечалась активность через [set_active](#set_active).

#### dwell_tracker <span class="mdx-badge"><span class="mdx-badge__icon">:material-eye:</span><span class="mdx-badge__text">DwellTracker</span></span>
Трекер просмотров - копит события и отправляет их батчами.

#### visibility <span class="mdx-badge"><span class="mdx-badge__icon">:material-eye-check:</span><span class="mdx-badge__text">VisibilityTracker</span></span>
Видимые посты и их таймеры: обновление статистики и скрытие постов, пока вас нет. Таймеры можно останавливать и запускать: `c.visibility.stop()` / `c.visibility.start()`.

<span id="set_active"></span>

## :material-cursor-default-click: Отметить активность
```py
c.set_active()
```
Вызывать при активностях клиента (скролл, движение мыши итд). Если активности нет дольше [dwell_inactive_timeout](../config.md#dwell_inactive_timeout-int), видимые посты скрываются, а при возвращении показываются снова (если пользователь не активен, посты считаются прочитанными). Работает только при [dwell_check_active](../config.md#dwell_check_active-bool).

## Сделать запрос
```py
from itd.enums import AuthLevel

res = c.request(
    method='post',
    url='v1/auth/refresh',
    params={},
    files={},
    level=AuthLevel.REFRESH
)
```
Сделать кастомный запрос на ИТД (эта функция используется внутри самого sdk).

### Параметры
#### method <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Метод запроса (`get`/`post`/`put`/`delete` и тд).

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Адрес запроса (без /api).

#### params <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-braces:</span><span class="mdx-badge__text">dict</span></span>
Параметры к запросу.

#### files <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-braces: [:material-text:, :material-code-parentheses:] :material-file:</span><span class="mdx-badge__text">dict[str, tuple[str, BufferedReader | bytes]]</span></span>
Файл для загрузке в формате `{'file': ('имя файла', 'содержание')}`

#### level <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AuthLevel](enums.md#authlevel)</span></span>
Требуемый уровень авторизации для запроса. По умолчанию `AuthLevel.ACCESS`.


### Ошибки
 - `InsufficientAuthLevelError` - недостаточный уровень авторизации

## Обновить статистики постов
```py
c.update_post_stats()
```
Обновить статистики (лайки, комментарии, репосты итд) просмотров в зоне видимости. Для добавления поста в зону видимости используйте `post.set_visible()`.

### Ошибки
 - `NotFoundError` - пост(ы) не найден(ы)

## Изменить пароль
```python
c.change_password(
    old='12345678',
    new='12345679'
)
```
!!! warning
    После сброса пароля `refresh token` сбросится. Нужно входить заново.

### Параметры

#### old <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Старый пароль.

#### new <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Новый пароль. 10+ символов, цифры, знаки пунктуации, латиница.

### Ошибки
 - `SamePasswordError` - пароли повторяются.
 - `InvalidOldPasswordError` - старый пароль неверный.
 - `InvalidPasswordError` - пароль не соответствует требованиям.

## Выйти
```python
c.logout()
```

!!! warning

    После выхода `refresh token` сбросится. Нужно входить заново.

## Сделать SSE запрос
```py
stream = c.request_sse('notifications/stream')
```
Открывает SSE-стрим (по нему работают [уведомления](notifications.md)). Токен обновляется так же, как и в обычном запросе.

## Обновить `access_token`
```python
token = c.refresh_auth()
```

### Ошибки
 - `SessionExpiredError` - рефреш токен истек (7 дней)
 - `SessionNotFoundError` - сессия не найдена (неправильный рефреш токен)
 - `SessionRevokedError` - сессия была ревокнута (выход из аккаунта)
