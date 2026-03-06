# Посты

## Создать пост
```python
post = c.create_post(
    content='чиенбурбе круче чем #иванговно',
    spans=[],
    wall_recipient_id=None,
    attachemnt_ids=[],
    poll=None
)
```
Должно быть указан хотя бы что-то одно (кроме `spans` и `wall_recipient_id`).

### Параметры

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Содержание поста.

#### spans <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-list-unordered-16: :material-text-short:</span><span class="mdx-badge__text">list[Span]</span></span>
Стилизация.

!!! example

    Для получения этого списка можно использовать парсинг (на данный момент поддерживается только `html`):

    ```python
    from itd.utils import parse_html

    c.create_post(*parse_html('<b>Толстый</b> <i>и</i> тонкий'))
    ```
    **Результат:** **толстый** *и* тонкий

    !!! info

        `*` - символ для "разархивации". `parse_html` возвращает список, который `*` разделяет на `content` (читый контент без тэгов) и `spans`

#### wall_recipient_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID получателя поста (для постов на стене). `Username` не работает.

#### attachment_ids <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-list-unordered-16: :material-identifier:</span><span class="mdx-badge__text">list[UUID]</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
ID вложений.

#### poll <span class="mdx-badge"><span class="mdx-badge__icon">:material-poll:</span><span class="mdx-badge__text">PollData</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Опросник.

!!! example

    ```python
    from itd.models.post import PollData

    c.create_post(
        poll=PollData(
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
 - `NotFound` - получатель поста не найден.
 - `Forbidden` - некоторые вложения не принадлежат вам или файл не существует. Вложения должны быть загружены вами через `upload_file`.
 - `ValidationError` - ошибка валидации, скорее всего из-за слишком большого количества символов.
 - `RequiresVerification` - нельзя загружать видео с неверифицированого аккаунта.

---

## Проголосовать
```python
poll = c.vote(
    id=UUID('aa612e16-eb1f-4323-89ce-4eacda133672'),
    option_ids=[UUID('f12c70c7-141e-4dff-9e5b-87f039c7ba58')]
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID поста.

#### option_ids <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-list-unordered-16: :material-identifier:</span><span class="mdx-badge__text">list[UUID]</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID опций для выбора (даже если в опросе можно выбрать только 1 вариант, все равно пишите как список).

!!! example

    === "1 опция"

        ```python
        c.vote(
            UUID('aa612e16-eb1f-4323-89ce-4eacda133672'),
            [UUID('f12c70c7-141e-4dff-9e5b-87f039c7ba58')]
        )
        ```

    === "несколько опций"

        ```python
        c.vote(
            UUID('a6135f23-bd75-441b-93b7-cf9cf04ef76c'),
            [
                UUID('6daf7815-b30a-4f98-8091-7a0e24caba6c'),
                UUID('3add69ee-4dae-4a81-9e4a-3e0fe77c7be0'),
                UUID('ac758a37-2cb5-45ba-b743-a0a11a2b8d3d')
            ]
        )
        ```

---

## Получить посты
```python
posts, pagination = c.get_posts(
    cursor=0,
    tab=PostsTab.POPULAR
)
```
Лимит - 20 постов (не меняется).

### Параметры

#### cursor <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Курсор для пагинации (из `pagination.next_cursor`).

!!! example

    ```python
    cursor = None

    while True:
        posts, pagination = c.get_posts(cursor=cursor)
        cursor = pagination.next_cursor
    ```

#### tab <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">PostsTab</span></span>
Вкладка.

 - `POPULAR`: Популярные
 - `FOLLOWING`: Подписки
 - `CLAN`: Лента кланов

!!! example

    ```python
    from itd.enums import PostsTab

    c.get_posts(tab=PostsTab.FOLLOWING)
    ```

---

## Получить пост
```python
post = c.get_post(
    id=UUID('c2f443df-61eb-4bfc-b52f-13aacecb9c46')
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID поста.

### Ошибки
 - `NotFound`

---

## Отредактировать пост
```python
content = c.edit_post(
    id=UUID('c2f443df-61eb-4bfc-b52f-13aacecb9c46'),
    content='Новое содержимое',
    spans=[]
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID поста.

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Новое содержимое.

#### spans  <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-list-unordered-16: :material-text-short:</span><span class="mdx-badge__text">list[Span]</span></span>
Стилизация. [см. Пример заполнения](#spans)

### Ошибки
 - `NotFound`
 - `Forbidden` - пост не ваш.
 - `ValidationError` - ошибка валидации.
 - `EditExpired` - истекло время на редактирование. Редактирвоание разрешено только в первые 48ч после его публикации.

---

## Удалить пост
```python
c.delete_post(
    id=UUID('c2f443df-61eb-4bfc-b52f-13aacecb9c46')
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID поста.

### Ошибки
 - `NotFound`
 - `Forbidden` - пост не ваш.

---

## Закрепить пост
```python
c.pin_post(
    id=UUID('c2f443df-61eb-4bfc-b52f-13aacecb9c46')
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID поста.

### Ошибки
 - `NotFound`
 - `Forbidden` - пост не на вашей стене.

---

## Репост
```python
post = c.repost(
    id=UUID('c2f443df-61eb-4bfc-b52f-13aacecb9c46'),
    content='Содрежимое'
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID поста.

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Дополнительная подпись.

### Ошибки
 - `NotFound`
 - `AlreadyReposted` - Пост уже репостнут.
 - `CantRepostYourPost` - Собственные посты нельзя репостить.
 - `ValidationError` - Ошибка валидации.

---

## Просмотреть пост
```python
c.view_post(
    id=UUID('c2f443df-61eb-4bfc-b52f-13aacecb9c46')
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID поста.

### Ошибки
 - `NotFound`

---

### Получить посты пользователя
```python
posts, pagination = c.get_user_posts(
    username_or_id='itd_sdk',
    limit=20,
    cursor=None
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID или `username` пользователя.

#### limit <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Лимит постов.

#### cursor <span class="mdx-badge"><span class="mdx-badge__icon">:material-timer:</span><span class="mdx-badge__text">datetime</span></span>
Курсор для пагинации (из `pagination.next_cursor`).

### Ошибки
 - `NotFound`

---

## Получить лайкнутые посты пользователя
```python
posts, pagination = c.get_liked_posts(
    username_or_id='itd_sdk',
    limit=20,
    cursor=None
)
```

### Параметры

#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID или `username` пользователя.

#### limit <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Лимит постов.

#### cursor <span class="mdx-badge"><span class="mdx-badge__icon">:material-timer:</span><span class="mdx-badge__text">datetime</span></span>
Курсор для пагинации (из `pagination.next_cursor`).

### Ошибки
 - `NotFound`
