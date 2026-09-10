# :material-post: Post

### Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID поста.

#### author <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-user:</span><span class="mdx-badge__text">[User](users.md#user)</span></span>
Автор поста.

#### created_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата создания поста.

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Содержание поста. `None`, если нет содержания (тогда должны быть вложения или опросник).

#### spans <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-text-short:</span><span class="mdx-badge__text">list[[Span](#span)]</span></span>
Стилизация (жирный, курсив, подчеркивание итд).

#### attachments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-file:</span><span class="mdx-badge__text">list[[PostAttach](files.md#postattach)]</span></span>
Вложения.

#### poll <span class="mdx-badge"><span class="mdx-badge__icon">:material-poll:</span><span class="mdx-badge__text">[Poll](#poll)</span></span>
Опросник.

#### comments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-comment:</span><span class="mdx-badge__text">[Comments](comments.md#comments)</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Комментарии.

#### first_comments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-comment:</span><span class="mdx-badge__text">list[[Comment](comments.md#comment)]</span></span>
Статичный список комментариев (при запросе на `GET api/posts/` отдается список максимум из трех комментариев).

#### likes_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество лайков.

#### comments_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество комментариев.

#### reposts_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество репостов.

#### views_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество просмотров.

#### edited_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата редактирования. `None`, если пост не редактировали.

#### is_liked <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Лайкнут ли пост.

#### is_reposted <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Репостнут ли пост.

#### is_viewed <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Просмотрен ли пост.

#### is_owner <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Являетесь ли вы владельцем поста.

#### is_pinned <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Закреплен ли пост. Отдает правильное значение только при получении поста из [`UserPosts`](#userposts).

#### dominant <span class="mdx-badge"><span class="mdx-badge__icon">:material-emoticon:</span><span class="mdx-badge__text">str</span></span>
Эмоджи клан, который чаще всего лайкал пост. `None`, если никто пока еще не лайкнул пост.

#### original_post <span class="mdx-badge"><span class="mdx-badge__icon">:material-post:</span><span class="mdx-badge__text">[Post](#post)</span></span>
Оригинальный пост, если этот - репост. `None`, если пост обычный.

#### wall_recipient_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID получателя поста. `None`, если пост создан не на чужой стене.

#### wall_recipient <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-user:</span><span class="mdx-badge__text">[User](users.md#user)</span></span>
Получать поста. `None`, если пост создан не на чужой стене.

#### vs <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Уникальный токен поста, для каждого пользователя он свой. Обновляется при получении поста. Испольуется при [просмотре поста](#view).

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Ссылка на пост.

#### link <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Тоже самое, что и [url](#url-str).

## Получить
```python
post = Post(
    id=UUID('c2f443df-61eb-4bfc-b52f-13aacecb9c46')
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID поста.

!!! note
    Для проверки на существование (`NotFoundError`) вызовите [`post.refresh()`](base.md#refresh) или любой аттрибут (если не включен [`config.load_on_getattr`](../config.md#load_on_getattr-bool))

## :fontawesome-solid-add: Создать
```python
from itd import Post

post = Post.new(
    content='чиенбурбе круче чем #иванговно',
    spans=[],
    wall_recipient=None,
    attachemnts=[],
    poll=None
)
```
Должно быть указан хотя бы что-то одно из `content`, `attachments` и `poll`.

### Параметры

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Содержание поста.

#### spans <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-text-short:</span><span class="mdx-badge__text">list[[Span](#span)]</span></span>
Стилизация (жирный, курсив, подчеркивание итд). Автоматически заполняется, если установлен [parse_mode](../config.md#parse_mode-parsemode). У ручного заполнения приоритет больше, чем у дефолтного (если у вас стоит `parse_mode` в конфиге, и вы напишите свой `spans`, применится ваш вариант).

#### wall_recipient <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier: | :fontawesome-solid-user:</span><span class="mdx-badge__text">UUID | User</span></span>
Получатель поста (для постов на стене). Может быть объектом пользователя или UUID.  
Для поста на стене также можно использовать `user.post()`.

#### attachments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-file: | :material-identifier: || :material-file: | :material-identifier:</span><span class="mdx-badge__text">list[UUID | File] | File | UUID</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Вложения. Может быть списком, объектом файла или UUID.

#### poll <span class="mdx-badge"><span class="mdx-badge__icon">:material-poll:</span><span class="mdx-badge__text">[NewPoll](#newpoll)</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Опросник.

!!! example

    ```python
    from itd import NewPoll

    Post.new(
        poll=NewPoll(
            'вапро', # (1)
            ['орешки макадамья', 'мне офень нгахвятся'], # (2)
            False # (3)
        )
    )
    ```

    1. Вопрос опроса
    2. Варианты ответа
    3. Можно ли ответить сразу несколько вариантов (по умолчанию - `False`)


### Ошибки
 - `NotFoundError` - получатель поста не найден.
 - `ForbiddenError` - некоторые вложения не принадлежат клиенту или не существуют. Вложения должны быть загружены одним и тем же клиентом через `upload_file`.
 - `ValidationError` - ошибка валидации, скорее всего из-за слишком большого количества символов.
 - `RequiresSubscriptionError` - для публикации видео нужна верификация или НУКСТА.
 - `BannedWordError` - в посте содержатся [запрещенные слова](https://itdsdk.qzz.io/banned-words).

## :material-vote: Проголосовать

=== "Через `post`"
    ```py
    post.vote(
        options=UUID('f12c70c7-141e-4dff-9e5b-87f039c7ba58')
    )
    ```

=== "Через `poll`"
    ```py
    post.poll.vote(
        options=UUID('f12c70c7-141e-4dff-9e5b-87f039c7ba58')
    )
    ```

=== "Через `option`"
    ```py
    post.poll.options[0].vote()
    ```

### Параметры

#### options <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-identifier: | :material-poll: || :material-identifier: | :material-poll:</span><span class="mdx-badge__text">list[UUID | [PollOption](#polloption)] | UUID | [PollOption](#polloption)</span></span> <span class="mdx-badge mdx-badge_required"> <span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Опции для голосования. Может быть списком, объектом опции (можно взять из `poll.options`) или UUID.

!!! example

    === "1 опция"

        ```python
        post.vote(UUID('f12c70c7-141e-4dff-9e5b-87f039c7ba58'))
        ```

    === "несколько опций"

        ```python
        post.vote(
            [
                UUID('6daf7815-b30a-4f98-8091-7a0e24caba6c'),
                UUID('3add69ee-4dae-4a81-9e4a-3e0fe77c7be0'),
                UUID('ac758a37-2cb5-45ba-b743-a0a11a2b8d3d')
            ]
        )
        ```

!!! tip
    Если вам надо переголосвать, просто отправьте запрос еще раз. Новый вариант перезапишет предыдущий. 

### Ошибки
 - `NotFoundError` (`Post`) - пост не найден.
 - `NotFoundError` (`Poll`) - опрос не найден (в посте нету опроса).
 - `OptionsNotBelongError` - опции не принадлежат к этом опросу.
 - `NotMultipleChoiceError` - в опросе можно проголосовать только за одну опцию.

## :material-heart: Лайкнуть
```python
likes_count = post.like()
```
Если пост уже лайкнут, ничего не произойдет.

### Ошибки
 - `NotFoundError` - пост не найден.

## :material-heart-off: Убрать лайк
```python
likes_count = post.unlike()
```
Если пост итак не лайкнут, ничего не произойдет.

### Ошибки
 - `NotFoundError` - пост не найден.

## :material-repeat: Репостнуть
```python
post = post.repost(
    content='Какой-то комментарий к репосту'
)
```

### Ошибки
 - `NotFoundError` - пост не найден.
 - `AlreadyRepostedError` - пост уже репостнут.
 - ~~`CantRepostYourselfPost` - нельзя репостить свои посты.~~ С версии ИТД 1.1.1 теперь можно репостить собственные посты (даже по несколько раз).
 - `ValidationError` - ошибка валидации (вероятно из-за слишком большого количества символов).
 - `BannedWordError` - в посте есть [запрещенные слова](https://itdsdk.qzz.io/banned-words).

<a id="view"></a>
## :material-account-switch: Для другого клиента
```py
post = post.for_client(client2)
```
Тот же пост, но привязанный к другому клиенту - все действия (лайк, просмотр, комментарий) пойдут от него. Свои данные новый объект загрузит сам, потому что у другого аккаунта и `is_liked`, и [vs](#vs-str) будут свои.

## :material-chart-line: Обновить статистику
```py
post.update_stats()
```
Обновляет только счетчики (лайки, комментарии, репосты, просмотры) (быстрее, чем полный `refresh()`). Эту же фукнцию использует [автообновление статистики видимых постов](../config.md#post_update_stats-bool).

После обновления вызывается `on_stats_update` - переопределите его, если надо на это реагировать:
```py
post.on_stats_update = lambda: print('новый лайк')
```

## :material-eye: Просмотреть
```python
post.view()
```

### Ошибки
 - `NotFoundError` - пост не найден.

## :material-pin: Закрепить
```python
post.pin()
```

### Ошибки
 - `NotFoundError` - пост не найден.
 - `ForbiddenError` - нет прав на закрепление (пост должен быть на вашей стене).

## :material-pin-off: Открепить
```python
post.unpin()
```

### Ошибки
 - `NotPinnedError` - пост не закреплен или не найден.

## :material-delete: Удалить
```python
post.delete()
```

### Ошибки
 - `NotFoundError` - пост не найден.
 - `ForbiddenError` - нету прав на удаление (пост должен быть на вашей стене).

## :material-delete-off: Восстановить
```python
post.restore()
```
Если пост итак не удален, ничего не произойдет.

### Ошибки
 - `NotFoundError` - пост не найден.
 - `ForbiddenError` - нету прав на восстановление (пост должен быть на вашей стене).

## :material-pencil: Редактировать
```python
edited_at = post.edit(
    content='Новый контент',
    spans=[]
)
```
!!! warning
    Редактировать пост можно только в первые 48 часов после публикации. После этого будет выходить ошибка `EditExpiredError`.

### Параметры

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Новое содержание поста.

#### spans <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-text-short:</span><span class="mdx-badge__text">list[Span]</span></span>
Стилизация. Автоматически заполняется, если установлен [parse_mode](../config.md#parse_mode-parsemode).

### Ошибки
 - `NotFoundError` - пост не найден.
 - `ForbiddenError` - нету прав на редактирование (вы должны быть автором поста).
 - `EditExpiredError` - истекло время на редактирование ("edit window expired").
 - `BannedWordError` - в посте есть [запрещенные слова](https://itdsdk.qzz.io/banned-words).

## :material-comment: Прокомментировать

=== "Через `post`"
    ```python
    post.add_comment(
        content='комментарие',
        attachments=[]
    )
    ```

=== "Через `comments`"
    ```python
    post.comments.new(
        content='комментарий новый только другой',
        attachments=[]
    )
    ```

=== "Через `Comment`"
    ```python
    from itd import Comment
    
    Comment.new(
        post.id,
        content='странный немножка комментарий',
        attachments=[]
    )
    ```

### Параметры

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Содержание комментария (стилизация не поддерживается на стороне ИТД).

#### attachments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-identifier: | :material-file: || :material-identifier: | :material-file:</span><span class="mdx-badge__text">list[UUID | File] | File | UUID</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Вложения. Может быть списком, объектом файла или UUID.

### Ошибки
 - `NotFoundError` - пост не найден.
 - `ValidationError` - ошибка валидации (вероятно из-за большого количества символов).
 - `BannedWordError` - в комментарии есть [запрещенные слова](https://itdsdk.qzz.io/banned-words).
 - `ForbiddenError` - некоторые вложения не принадлежат клиенту или не существуют. Вложения должны быть загружены одним и тем же клиентом через `upload_file`.
 - `RequiresSubscriptionError` - для загрузки видео требуется верификация или подписка НУКСТА.

## :octicons-report-16: Пожаловаться
```python
from itd.enums import ReportReason

post.report(
    reason=ReportReason.SPAM,
    description='описание'
)
```

### Параметры
#### reason <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-report-16:</span><span class="mdx-badge__text">[ReportReason](enums.md#reportreason)</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Причина жалобы.

#### description <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Описание жалобы.

### Ошибки
 - `NotFoundError` - пост не найден.
 - `AlreadyReportedError` - жалоба уже отправлена.
 - `ValidationError` - ошибка валидации (слишком длинное описание).

## :material-link: Получить ссылку на пост
```python
link = post.url
```
или
```python
link = post.link
```

---

# :material-text-short: Span

## Аттрибуты
#### length <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Длина спана.

#### offset <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Смещение.

#### type <span class="mdx-badge"><span class="mdx-badge__icon">:material-text-short:</span><span class="mdx-badge__text">[SpanType](enums.md#spantype)</span></span>
Тип спана.

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Ссылка. `None`, если `type` != `SpanType.LINK`.

#### tag <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Хэштэг. `None`, если `type` != `SpanType.HASHTAG`.

---

# :material-poll: Poll
Опрос.

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID опроса.

#### post_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID поста, к которому прикреплен опросник.

#### created_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата создания поста.

#### question <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Вопрос опроса.

#### options <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-poll:</span><span class="mdx-badge__text">list[[PollOption](#polloption)]</span></span>
Варианты ответов.

#### multiple <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Можно ли выбирать несколько вариантов ответа.

#### is_voted <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Проголосовал ли пользователь в опросе.

#### voted_option_ids <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-identifier:</span><span class="mdx-badge__text">list[UUID]</span></span>
ID вариантов, за которые проголсовал пользователь. `[]`, если [пользователь не голосовал в опросе](#is_voted-bool).

#### total_votes <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Общее количество голосов. `0`, если [пользователь не голосовал в опросе](#is_voted-bool).


## :material-vote: Проголосовать
```py
poll.vote(
    options=UUID('f12c70c7-141e-4dff-9e5b-87f039c7ba58')
)
```

### Параметры

#### options <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-identifier: | :material-poll: || :material-identifier: | :material-poll:</span><span class="mdx-badge__text">list[UUID | [PollOption](#polloption)] | UUID | [PollOption](#polloption)</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Опции для голосования. Может быть списком, объектом опции (можно взять из `poll.options`) или UUID.


### Ошибки
 - `NotFoundError` (`Post`) - пост не найден.
 - `NotFoundError` (`Poll`) - опрос не найден (в посте нету опроса).
 - `OptionsNotBelongError` - опции не принадлежат к этом опросу.
 - `NotMultipleChoiceError` - в опросе можно проголосовать только за одну опцию.

---

# :material-poll: PollOption
Вариант ответа в опросе.

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID варианта.

#### text <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Содержание варианта.

#### votes <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Общее количество голосов за вариант. `0`, если [пользователь не голосовал в опросе](#is_voted-bool).

#### position <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Позиция варианта в опросе (индекс).


## :material-vote: Проголосовать
```py
option.vote()
```

---

# :fontawesome-solid-add: :material-poll: NewPoll
Модель для создания нового опроса.

```py
poll = NewPoll(
    question='чипс лейз без краба иле 10 детей',
    options=[
        'вкуссненькие чипсеки',
        '10 детей',
        'нет'
    ],
    multiple=False
)
```
#### question <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Вопрос опроса.

#### options <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-text:</span><span class="mdx-badge__text">list[str]</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Варианты ответов.

#### multiple <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Можно ли выбирать несколько вариантов ответа. По умолчанию `False`.

!!! question
    Изначально планировалось объединить модель с [`Poll`](#poll), однако из-за разницы в полях (в объекте нужно указать `post_id`, который еще не создан) этого сделать не получилось.
    Кстати если у вас есть идея как это можно реализовать лучше, открывайте issue.

---

## :material-content-copy: СОздать из существующего опроса
```py
poll = NewPoll.from_poll(post.poll)
```
Копирует вопрос, варианты и режим у [Poll](#poll) (можно склонировать чужой опрос в своем посте).

# :material-code-brackets: :material-post: Posts
Лента постов.

!!! note "source и source_context"
    У каждого списка постов есть `source` ([ViewSource](enums.md#viewsource)) и `source_context` - откуда взялись посты. Они проставляются сами (лента, профиль, хэштэг итд) и уходят в статистику [просмотров](#view), так что менять их обычно не нужно.

- [x] has_more
- [ ] total

## Лента
```python
posts = Posts()
```

### Параметры
#### tab <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[PostsTab](enums.md#poststab)</span></span>
Вкладка постов. По умолчанию `PostsTab.POPULAR`.

 Также вкладку можно задать через клаcсметод:

### :fontawesome-solid-arrow-trend-up: Популярное
```python
posts = Posts.popular()
```
или
```python
posts = Posts.trending()
```

### :fontawesome-solid-user-plus: Подписки
```python
posts = Posts.following()
```

### :material-emoticon: Лента клана
```python
posts = Posts.clan()
```

## Ошибки при получении
 - `ValidationError` - ошибка валидации (из-за слишком большого лимита батча).

## :fontawesome-solid-user: UserPosts
Посты пользователя.

- [x] has_more
- [ ] total

=== "Через `UserPosts`"
    ```python
    from itd.enums import UserPostSorting
    
    posts = UserPosts(
        user='fdg',
        sorting=UserPostSorting.NEW
    )
    ```

=== "Через `User`"
    ```python
    from itd import User
    
    posts = User('fdg').posts
    ```

### Параметры

#### user <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier: | :fontawesome-solid-user:</span><span class="mdx-badge__text">UUID | User</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Пользователь для получения постов с его стены. Может быть объектом пользователя или UUID.

#### sort <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">UserPostSorting</span></span>
Сортировка постов. По умолчанию `UserPostSorting.NEW`.

Также вкладку можно задать через клаcсметод:

### :new: Новые посты
```python
posts = UserPosts.new('fdg')
```


### :fontawesome-solid-arrow-trend-up: Популярные посты
```python
posts = UserPosts.popular('fdg')
```

## Ошибки при получении
 - `NotFoundError` - пользователь не найден.
 - `ValidationError` - ошибка валидации (может быть из-за слишком большого лимита батча).

### :octicons-clock-16: Ожидание поста
```py
post = posts.wait_for_post(
    delay=5
)
```
Ждет пока появится новый пост и возвращает его.

#### delay <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Задержка при проверке (без учета anti-ratelimit). По умолчанию `5`.

## :material-heart: LikedPosts
Лайкнутые посты пользователя.

- [x] has_more
- [ ] total

=== "Через `LikedPosts`"
    ```python
    posts = LikedPosts('fdg')
    ```

=== "Через `User`"
    ```python
    posts = User('fdg').liked_posts
    ```

## Ошибки при получении
 - `NotFoundError` - пользователь не найден.
 - `ValidationError` - ошибка валидации (может быть из-за слишком большого лимита батча).

### :octicons-clock-16: Ожидание поста
```py
post = posts.wait_for_post(
    delay=5
)
```
Ждет пока появится новый пост и возвращает его.

#### delay <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Задержка при проверке (без учета anti-ratelimit). По умолчанию `5`.

## :fontawesome-solid-hashtag: HashtagPosts
Посты по хэштэгу.

- [x] has_more
- [x] total

=== "Через `HashtagPosts`"
    ```python
    posts = HashtagPosts('fdg')
    ```

=== "Через `Hashtag`"
    ```python
    from itd import Hashtag
    
    posts = Hashtag('fdg').posts
    ```

### Параметры
#### hashtag <span class="mdx-badge"><span class="mdx-badge__icon">:material-text: | :fontawesome-solid-hashtag:</span><span class="mdx-badge__text">str | Hashtag</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Хэштэг. Может быть объектом хэштэга или строкой (без "#").

## Ошибки при получении
 - `TooLargeError` - слишком длинный хэштэг.
 - `NotFoundError` - хэштэг не найден.
 - `ValidationError` - ошибка валидации (слишком большой лимит).

### :octicons-clock-16: Ожидание поста
```py
new_posts = posts.wait_for_posts(
    delay=5,
    find_post=True
)
```
Ждет, пока по хэштэгу появятся новые посты, и возвращает их списком (`None`, если `find_post=False`). Проверяет через [posts_count](hashtags.md#posts_count-int) у хэштэга, так что за один раз может появиться сразу несколько постов.

#### delay <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">float</span></span>
Задержка при проверке (без учета anti-ratelimit). По умолчанию `5`.

#### find_post <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Нужно ли искать новый пост. Увеличивает время на поиск (до начала проверки и после находа различия в количестве берет полный список постов). По умолчанию `True`.
