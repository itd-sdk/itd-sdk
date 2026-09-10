# :fontawesome-solid-user: User

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID пользователя.

#### username <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Username.

#### display_name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Отображаемое имя пользователя.

#### avatar <span class="mdx-badge"><span class="mdx-badge__icon">:material-emoticon:</span><span class="mdx-badge__text">str</span></span>
Эмоджи-клан (аватар) пользователя.

#### verified <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Верифицирован ли пользователь.

#### pin <span class="mdx-badge"><span class="mdx-badge__icon">:material-pin:</span><span class="mdx-badge__text">Pin</span></span>
Установленный пин пользователя. `None`, если пользователь не установил пин.

#### banner <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Ссылка на баннер пользователя. `None`, если баннер не установлен.

#### bio <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Био пользователя. `None`, если он не задал описание или [аккаунт приватный](#is_private-bool).

!!! note
    Если пользователь поставит в био пробел (`" "`), то значение будет `""` (хотя если бы он оставил поле пустое, то значение было бы `None`).

#### followers <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :fontawesome-solid-user:</span><span class="mdx-badge__text">list[User]</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Статичный список подписчиков. Максимальная длина - `20`, отсортирован по дате подписки (первые 20 подписавшихся). Если еще не загружен, автоматически подгрузится. Пустой список, если пользователь заблокирован или [аккаунт приватный](#is_private-bool).

#### following <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :fontawesome-solid-user:</span><span class="mdx-badge__text">list[User]</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Статичный список подписок (на кого подписан пользователь). Максимальная длина - `20`, отсортирован по дате подписки (первые 20 подписок). Если еще не загружен, автоматически подгрузится. Пустой список, если [пользователь заблокирован](#is_blocked_by-bool) или [аккаунт приватный](#is_private-bool).

#### is_following <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Подписаны ли вы на пользователя. Автоматически изменяется при [`user.follow()`](#follow)/[`user.unfollow()`](#unfollow).

#### is_followed_by <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Подписаны ли пользователь на вас.

#### is_blocking <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Заблокировали ли вы пользователя. Автоматически изменяется при [`user.block()`](#block)/[`user.unblock()`](#unblock).

#### is_blocked_by <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Заблокировал ли вас пользователь.

!!! info
    Если [`is_blocking`](#is_blocking-bool) или [`is_blocked_by`](#is_blocked_by-bool) == `True`, то большинство данных (такие как `bio`, `followers`, `posts`, `created_at` и тд) будут `None`.

#### blocked_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата блокировки. Известна только когда [вы заблокировали пользователя](#is_blocking-bool). `None`, если пользователь заблокировал вас (а не вы его) или никто не блокировал друг друга.

#### followers_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество подписчиков (отличается от `len([followers](#followers-list-user))`, так как самих пользователей показывает только первые 20шт). `None`, если [аккаунт приватный](#is_private-bool).

#### following_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество подписок (отличается от `len([following](#following-list-user))`, так как самих пользователей показывает только первые 20шт). `None`, если [аккаунт приватный](#is_private-bool).

#### posts_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество постов. `None`, если [аккаунт приватный](#is_private-bool)).

#### wall_access <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AccessType](enums.md#accesstype)</span></span>
Доступ к созданию постов на стене пользователя. `None`, если [пользователь заблокирован](#is_blocked_by-bool).

#### likes_visibility <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AccessType](enums.md#accesstype)</span></span>
Доступ к лайкнутым постам пользователя. `None`, если [пользователь заблокирован](#is_blocked_by-bool).

#### is_private <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Приватный ли аккаунт пользователя. `None`, если вы подписаны на пользователя (при подписке ограничения приватности пропадают, и нельзя узнать, приватный вообще пользователь или нет).

!!! info
    Если `is_private` == `True`, то большинство данных (такие как `bio`, `followers`, `posts`, `created_at` и тд) будут `None`. Для получения реальных значений нужно [подписаться на пользователя](#follow).

#### is_subscribed <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Есть ли у пользователя подписка ИТД НУСКТА.

#### last_seen <span class="mdx-badge"><span class="mdx-badge__icon">:material-clock-time-two-outline:</span><span class="mdx-badge__text">[LastSeen](#lastseen)</span></span>
Относительная дата последней активности (`недавно`, `несколько минут назад` и тд). `None`, если пользователь заблокирован, приватный аккаунт или показ скрыт в настройках приватности пользователя.

#### online <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Находится ли пользователь в онлайне.

#### pinned_post_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID закрепленного поста. `None`, если у пользователя нет закрепа.

#### created_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата создания аккаунта. `None`, если пользователь заблокирован или у него приватный аккаунт.

#### posts <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-post:</span><span class="mdx-badge__text">[UserPosts](posts.md#userposts)</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Список постов.

#### liked_posts <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-post:</span><span class="mdx-badge__text">[LikedPosts](posts.md#likedposts)</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Список лайкнутых постов.

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Ссылка на пользователя.

#### link <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Тоже самое, что и [url](#url-str-property).

#### can_message <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Можно ли писать пользователю. Хоть и ЛС в ИТД пока нет, на бэкенде это поле уже есть (но поменять его сейчас нельзя).

#### can_post_on_wall <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Можете ли вы [написать на стену](#_6) пользователю (считается из [wall_access](#wall_access-accesstype) и статуса подписки).

#### can_see_liked_posts <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Можно ли смотреть [лайки](#liked_posts-likedposts-property) пользователя (считается из [likes_visibility](#likes_visibility-accesstype) и статуса подписки).

## :material-account-switch: Для другого клиента
```python
user = user.for_client(client2)
```
Тот же пользователь, но от лица другого клиента - подписки, блокировки и права (`is_following`, `can_post_on_wall` итд) у него свои, поэтому данные загрузятся заново.

## Получить пользователя
```python
user = User('itd_sdk')
```
Принимает как ID, так и username.

### Получить пользователя по ID
```py
user = User.by_id('587167e9-25ad-4948-afc0-2ee5bc9097ea')
```

### Получить пользователя по username
```py
user = User.by_username('itd_sdk')
```
или
```py
user = User.by_u('itd_sdk')
```

!!! abstract
    если передаете ID в `User(xxx)`, он обязательно должно быть в типе `UUID`. Если вам нужно передать ID как строку, используйте `User.by_id(xxx)`. `User.by_u(xxx)` принимает только str (без лишних проверок на UUID).

### Получить текущего пользователя
```py
user = User.me()
```
или
```py
user = Me()
```
см. [документацию для Me()](#me)

### Параметры
#### username_or_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-text: | :material-identifier:</span><span class="mdx-badge__text">str | UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Username или ID пользователя.

!!! note
    Для проверки на существование (`NotFoundError`) вызовите [`user.refresh()`](#_9) или любой аттрибут (если не включен [`config.load_on_getattr`](../config.md#load_on_getattr-bool))

## :octicons-report-16: Пожаловаться
```py
report = user.report(
    reason=ReportReason.SPAM,
    description='описание'
)
```
Пожаловаться на пользователя.

### Параметры
#### reason <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-report-16:</span><span class="mdx-badge__text">[ReportReason](enums.md#reportreason)</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Причина жалобы.

#### description <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Описание жалобы.

### Ошибки
 - `NotFoundError` - пользователь не найден.
 - `AlreadyReportedError` - вы уже оставляли жалобу на этого пользователя.
 - `ValidationError` - ошибка валидации (слишком длинное описание).

 <a id="follow"></a>
## :fontawesome-solid-user-plus: Подписаться
```py
followers_count = user.follow()
```
Подписаться на пользователя.

### Ошибки
 - `NotFoundError` - пользователь не найден.
 - `AlreadyFollowingError` - вы уже подписаны на этого пользователя.
 - `TooLargeError` - слишком длинный юзернейм.
 - `CantFollowYouself` - нельзя подписываться на самого себя.
 - `UserBlockedError` - пользователь заблокирован (или вы заблокировали его).
 - `TargetUserBannedError` - пользователь забанен.

<a id="unfollow"></a>
## :fontawesome-solid-user-minus: Отписаться
```py
followers_count = user.unfollow()
```
Отписаться от пользователя.

### Ошибки
 - `NotFoundError` - пользователь не найден.
 - `TooLargeError` - слишком длинный юзернейм.
 - `TargetUserBannedError` - пользователь забанен.

<a id="block"></a>
## :material-block-helper: Заблокировать
```py
user.block()
```
!!! warning
    После блока подписка слетает: если вы были подписаны на пользователя, то автоматически отписываетесь, и наоборот, если пользователь был подписан на вас подписка пропадает. Даже после [unblock()](#unblock) подписка не восстановится (нужно подписываться заново вручную).

### Ошибки
 - `NotFoundError` - пользователь не найден.
 - `TooLargeError` - слишком длинный юзернейм.
 - `AlreadyBlockedError` - пользователь итак заблокирован.
 - `CantBlockYourselfError` - нельзя заблокировать самого себя.
 - `TargetUserBannedError` - пользователь забанен.

 <a id="unblock"></a>
## Разблокировать
```py
user.unblock()
```

### Ошибки
 - `NotFoundError` - пользователь не найден.
 - `TooLargeError` - слишком длинный юзернейм.
 - `NotBlockedError` - пользователь итак не заблокирован.
 - `TargetUserBannedError` - пользователь забанен.

## :material-post: Пост на стене
```py
user.post(
    content='содержание',
    spans=[],
    attachments=[],
    poll=NewPoll(
        question='тест',
        options=['1', '2', '3', '4', '5'],
        multiple=True
    )
)
```

### Параметры
#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Содержание поста.

#### spans <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-text-short:</span><span class="mdx-badge__text">list[Span]</span></span>
Стилизация (жирный, курсив, подчеркивание итд). Автоматически заполняется, если установлен [parse_mode](../config.md#parse_mode-parsemode). У ручного заполнения приоритет большем, чем у дефолтного (если у вас стоит parse_mode в конфиге, и вы напишите свой spans, применится ваш вариант).

#### wall_recipient <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier: | :fontawesome-solid-user:</span><span class="mdx-badge__text">UUID | User</span></span>
Получатель поста (для постов на стене). Может быть объектом пользователя или UUID.  
Для поста на стене также можно использовать `user.post()`.

#### attachments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-file: | :material-identifier: || :material-file: | :material-identifier:</span><span class="mdx-badge__text">list[[File](files.md#file) | UUID] | [File](files.md#file) | UUID</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Вложения. Может быть списком, объектом файла или UUID.

#### poll <span class="mdx-badge"><span class="mdx-badge__icon">:material-poll:</span><span class="mdx-badge__text">NewPoll</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Опросник.

### Ошибки
 - `NotFoundError` - получатель поста не найден.
 - `ForbiddenError` - некоторые вложения не принадлежат клиенту или не существуют. Вложения должны быть загружены одним и тем же клиентом через `upload_file`.
 - `ValidationError` - ошибка валидации, скорее всего из-за слишком большого количества символов.
 - `RequiresSubscriptionError` - для публикации видео нужна верификация или НУКСТА.
 - `BannedWordError` - в посте содержатся [запрещенные слова](https://itdsdk.qzz.io/banned-words).

## :material-refresh: Обновить
```python
user.refresh()
```

### Ошибки
 - `NotFoundError` (`User`) - пользователь не найден.
 - `TooLargeError` - слишком дилнный юзернейм.
 - `NotFoundError` (`Profile`) - профиль не найден (пользователь только привязал почту, но еще не добавил эмоджи клан и имя)
 - `TargetUserBannedError` - пользователь забанен.

## Выполнить действия для постов на стену
```py
is_succeed = user.complete_actions_for_wall_access()
```

## Выполнить действия для просмотра лайков
```py
is_succeed = user.complete_actions_for_likes_visibility()
```

---

# Me

## Аттрибуты
!!! note
    Аттрибуты отличаются от обычного пользователя (большинство полей не могут быть `None`).

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID пользователя.

#### username <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Username.

#### display_name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Отображаемое имя пользователя.

#### avatar <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Эмоджи-клан (аватар) пользователя.

#### verified <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Верифицирован ли пользователь.

#### pin <span class="mdx-badge"><span class="mdx-badge__icon">:material-pin:</span><span class="mdx-badge__text">Pin</span></span>
Установленный пин пользователя. `None`, если вы не установили пин.

#### banner <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Ссылка на баннер пользователя. `None`, если баннер не установлен.

#### bio <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Био пользователя. `None`, если био пустое.

#### followers_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество подписчиков.

#### following_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество подписок.

#### posts_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество постов.

#### wall_access <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AccessType](enums.md#accesstype)</span></span>
Доступ к созданию постов на вашей стене.

#### likes_visibility <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AccessType](enums.md#accesstype)</span></span>
Доступ к лайкнутым постам.

#### is_private <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Приватный ли у вас аккаунт.

#### is_phone_verified <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Верифицирован ли номер телефона (подтвережден через телеграм).

#### subscription <span class="mdx-badge"><span class="mdx-badge__icon">:material-diamond:</span><span class="mdx-badge__text">[Subscription](#subscription)</span></span>
Данные о подписке.

#### created_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата создания аккаунта.

#### followers <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :fontawesome-solid-user:</span><span class="mdx-badge__text">Followers</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Список подписчиков.

#### following <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :fontawesome-solid-user:</span><span class="mdx-badge__text">Following</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Список подписок.

#### blocked <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :fontawesome-solid-user:</span><span class="mdx-badge__text">Blocked</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Список заблокированных пользователей.

#### posts <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-post:</span><span class="mdx-badge__text">UserPosts</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Список постов.

#### liked_posts <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-post:</span><span class="mdx-badge__text">[LikedPosts](posts.md#likedposts)</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Список лайкнутых постов.

#### pins <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-pin:</span><span class="mdx-badge__text">list[[Pin](#pin)]</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Список пинов.

#### profile <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-user:</span><span class="mdx-badge__text">[Profile](#profile)</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Профиль пользователя (чем-то похож на сам `Me`, но берется отдельным зарпосом `/api/profile`).

#### privacy <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-user-lock:</span><span class="mdx-badge__text">[Privacy](#privacy)</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Данные приватности пользователя.

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Ссылка на пользователя.

#### link <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Тоже самое, что и [url](#url-str-property_1).

## Конвертировать в User
```py
user = me.to_user()
```
В ответ отдает [`User`](#user).

## :fontawesome-solid-user-edit: Обновить профиль
```python
from itd.enums import UNSET

profile = me.update(
    bio='био',
    display_name='имя',
    username='username',
    banner_id=UNSET
)
```

### Обновить из текущих аттрибутов
```py
me.username = 'username2'
me.bio = 'другое био'
me.update_from_fields()

```

### Параметры
#### username <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Новый юзернейм.

#### display_name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Новое имя.

#### bio <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Биография (о себе).

#### banner_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier: | UNSET</span><span class="mdx-badge__text">UUID | Unset</span></span>
ID файла баннера.

!!! tip

    Для удаления баннера используйте `UNSET`:

    ```python
    from itd.enums import UNSET

    me.update(banner_id=UNSET)
    ```

### Ошибки
 - `ValidationError` - ошибка валидации (например слишком длинное имя).
 - `RequiresVerificationError` - требуется верификация для загрузки GIF-баннера.
 - `UsernameTakenError` - username уже занят.

## :fontawesome-solid-user-lock: Обновить настройки приватности
```python
from itd.models.user import UserPrivacyData
from itd.enums import AccessType

privacy = me.update_privacy(
    is_private=False,
    wall_access=AccessType.EVERYONE,
    likes_visibility=AccessType.FOLLOWERS,
    show_last_seen=True
)
```

### Параметры
#### is_private <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Приватный профиль. Посты не будут попадать в ленту, профиль будет виден только для подписчиков.

#### wall_access <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AccessType](enums.md#accesstype)</span></span>
Доступ к стене.

#### likes_visibility <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AccessType](enums.md#accesstype)</span></span>
Доступ к лайкнутым постам.

#### show_last_seen <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Показывать дату последнего захода.

### Ошибки
 - `ValidationError` (скорее всего ошибка в sdk)

## :material-delete: Удалить аккаунт
```python
me.delete()
```

!!! danger
    У вас будет 30 дней на восстановление аккаунта (см. восстановление аккунта ниже). После этого аккаунт безвозратно удалится.

!!! tip "Интересный факт"
    Сам аккаунт не удалится из базы, просто `can_restore` заменится на `False`.
    <!-- Тут должен быть скрин от итд статуса где он писал что ИТД не удаляет ак, но я его не нашел -->

### Ошибки
 - `AlreadyDeletedError` - аккаунт уже удален.

## :material-delete-off: Восстановить аккаунт
```python
me.restore()
```

### Ошибки
 - `NotDeletedError`: Аккаунт итак не удален.

!!! note
    Здесь также должна быть ошибка, что уже слишком поздно, но к сожалению у меня нет дополнительного аккаунта для удаления, чтобы посмотреть как она называется 🫤.

## :material-pin: Установить пин
```py
me.set_pin(me.pins[0])
```

### Параметры
#### pin <span class="mdx-badge"><span class="mdx-badge__icon">:material-text: | :material-pin:</span><span class="mdx-badge__text">str | Pin</span></span>
Объект пина или слаг. Если None - устанавливается первый из списка.

### Ошибки
 - `ValueError` - список пинов пустой (если pin is None).
 - `PinNotOwnedError` - пин не принадлежит вам.

## :material-pin-off: Снять пин
```py
me.remove_pin()
```
Если пин итак не установлен, ничего не произойдет.

---

# :material-diamond: Subscription

### Аттрибуты
#### active <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Активна ли подписка.

#### expires_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата истечения подписка. `None`, если подписка не активирована.

#### auto_renewal <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Включено ли автопродление (сейчас вроде как не используется).

!!! tip "Интересный факт"
    Изначально в ИТД хотели сделать свою полноценную платежную систему (видно по тому, что в базе есть такие поля как номер банковской карты, CVC, срок годности и тд), но что-то не получилось (наверное юридическое), и в итоге они просто сделали интеграцию с Юкасса, которая хэндлит все эти данные сама (в том числе auto renewal). Поэтому auto_renewal сейчас ничего не делает, а также он убран с фронтенда.

#### payment_methods <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-credit-card:</span><span class="mdx-badge__text">list[dict]</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Привязанные способы оплаты - так, как их отдает ИТД. Каждый раз ходит в API.

## :material-credit-card: Оплатить попдиску
```py
link = subscription.pay()
```
В ответ приходит ссылка на оплату.

## :material-autorenew: Установить значение авто-проделния
```py
enabled = subscription.set_auto_renewal(True)
```

### Параметры
#### enabled <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Значение авто-продления.

## :material-autorenew: Переключить авто-продление
```py
enabled = subscription.toggle_auto_renewal()
```

---

# :material-pin: Pin

### Аттрибуты
#### slug <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Слаг пина латиницей (например `epepuy_202605_78`).

#### name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Название пина (например `78 баллов за написание Единственного Первого Экзамена по Ютубу`).

#### description <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Ивент (например `ЕПЭПЮ 2026 (Май, 2026г)`).

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Ссылка на изображение пина.

#### granted_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата выдачи пина. Есть только при получении пинов из списка (`me.pins`).

## Установить
```py
pin.set()
```

## Снять
```py
pin.remove()
```
Если этот пин итак не установлен, ничего не произойдет.

---

# :fontawesome-solid-user: Profile

### Аттрибуты
#### user <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-user:</span><span class="mdx-badge__text">[ProfileUser](#profileuser)</span></span>
Данные о пользователе (похож на `Me`). `None`, если `deleted`, `profile_required` или `banned` == `True` или `authenticated` == `False`.

#### authenticated <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Аутентифицирован ли пользователь.

#### banned <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Забанен ли пользователь.

#### deleted <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Удален ли пользователь.

#### can_restore <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Можно ли восстановить аккаунт.

#### message <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Если пользоатель удален, сообщение об ошибке `Your account has been deleted` (вроде бы при бане тоже используется).

#### profile_required <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли создать профиль.

#### user_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID пользователя. `None`, если `authenticated` == `False` или `ProfileUser` != `None` (если есть `ProfileUser`, то надо брать из него).

#### roles <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-account-supervisor-outline:</span><span class="mdx-badge__text">list[[Role](enums.md#role)]</span></span>
Роли пользователя. `None`, если `ProfileUser` != `None` (если есть `ProfileUser`, то надо брать из него).

---

## ProfileUser

### Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID пользователя.

#### username <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Username.

#### display_name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Отображаемое имя пользователя.

#### avatar <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Эмоджи-клан (аватар) пользователя.

#### verified <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Верифицирован ли пользователь.

#### bio <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Био пользователя. `None`, если био пустое.

#### is_phone_verified <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Верифицирован ли номер телефона (подтвережден через телеграм).

#### roles <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-account-supervisor-outline:</span><span class="mdx-badge__text">list[[Role](enums.md#role)]</span></span>
Роли пользователя.

---

# :fontawesome-solid-user-lock: Privacy

## Аттрибуты
!!! info
    Все аттрибуты кроме `show_last_seen` автоматически подгрузятся из модели пользователя (если она была загружена).

#### wall_access <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AccessType](enums.md#accesstype)</span></span>
Доступ к созданию постов на вашей стене.

#### likes_visibility <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AccessType](enums.md#accesstype)</span></span>
Доступ к лайкнутым постам.

#### is_private <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Приватный ли у вас аккаунт.

#### show_last_seen <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли показывать дату последнего входа другим пользователям.

### Обновить настройки
```py
from itd.enums import AccessType

me.privacy.update(
    wall_access=AccessType.NOBODY,
    likes_visibility=AccessType.FOLLOWERS,
    is_private=False,
    show_last_seen=True
)
```

### Обновить настройки из аттрибутов
```py
me.privacy.wall_access = AccessType.EVERYONE
me.privacy.is_private = True
me.privacy.update_from_fields()
```

---

# LastSeen

## Аттрибуты

#### unit <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[LastSeenUnit](enums.md#lastseenunit)</span></span>
Юнит (минута, час, день и тд).

#### value <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество юнитов. `None`, если юнит неисчисляемый (`long_ago`, `this_week`, `just_now`, `recently`, `this_month`).

!!! tip
    Для получения человеко читаемого формата используйте `str(last_seen)`:
    ```py
    last_seen = LastSeen(unit=LastSeenUnit.MINUTES, value=2) # пример как может выглядеть user.last_seen

    str(last_seen) # 2 минуты назад
    ```
