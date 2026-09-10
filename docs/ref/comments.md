# Comment

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID комментария.

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Содержание комментария.

#### created_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата создания комментария.

#### author <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-user:</span><span class="mdx-badge__text">[User](users.md#user)</span></span>
Автор комментария.

#### likes_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество лайков.

#### replies_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество ответов.

#### is_liked <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Лайкнут ли комментарий.

#### attachments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-file:</span><span class="mdx-badge__text">list[[CommentAttach](files.md#commentattach)]</span></span>
Вложения комментария.

#### replies <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-comment:</span><span class="mdx-badge__text">[Replies](#replies)</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Ответы.

#### first_replies <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-comment:</span><span class="mdx-badge__text">list[[Comment](#comment)]</span></span>
Статичный список ответов (при получении комментариев к каждому коменту отдается список максимум из трех ответов). `[]`, если сам комментарий - ответ.

#### reply_to <span class="mdx-badge"><span class="mdx-badge__icon">:fontawesome-solid-user:</span><span class="mdx-badge__text">[User](users.md#user)</span></span>
Автор комментария, на который отвечает этот комментарий. Обычно `nickname` с этого пользвоателя ставят перед началом содержания (`@{reply_to.username}, {content}`). `None`, если комментарий ни на что не отвечает (не ответ).

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Ссылка на комментарий.

#### link <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Тоже самое, что и [url](#url-str-property).

#### is_reply <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Является ли комментарий ответом на другой (то есть заполнен ли [reply_to](#reply_to-user)).

#### is_owner <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Ваш ли это комментарий.

#### can_edit <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Можно ли [отредактировать](#_4) - только свой комментарий.

#### can_delete <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Можно ли [удалить](#_3) - свой комментарий или любой комментарий под своим постом.

#### can_report <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Можно ли пожаловаться - на свой комментарий нельзя.

!!! note
    `can_delete` знает про пост, только если комментарий получен через пост (`post.comments`). У отдельно созданного комментария будет `AssertionError`.

## :material-reply: Ответить
```py
reply = comment.reply(
    content='123',
    attachments=[],
    user_id=None
)
```

### Параметры
#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Содержание ответа.

#### attachments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-file: | :material-identifier: || :material-file: | :material-identifier:</span><span class="mdx-badge__text">list[[File](files.md#file) | UUID] | [File](files.md#file) | UUID</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Вложения.

#### user_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
Автор другого комментария, на который отвечать. По умолчанию берется текущий автор комментария. Если указанный пользователь не комментаривал пост, комментарий создастся, но не будет виден на клиенте и не будет приходить в API.

### Ошибки
 - `ValidationError` - ошибка валидации (слишком длинный ответ).
 - `NotFoundError` (`Comment`) - основной комментарий не найден.
 - `NotFoundError` (`User`) - пользователь, которому нужно ответить, не найден.
 - `BannedWordError` - в ответе содержутся [заперщенные слова](https://itdsdk.qzz.io/banned-words).
 - `ForbiddenError` - некоторые файлы не принадлежат вам.
 - `RequiresSubscriptionError` - для загрузки видео нужна подписка ИТД НУКСТА.

## :fontawesome-solid-add: Создать 
```py
comment = Comment.new(
     '6c175aef-f8f9-46b1-ad78-cb756b0430cb',
     content='123',
     attachments=[]
)
```

#### post_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID поста.

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Содержание комментария.

#### attachments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-identifier: | :material-file: || :material-identifier: | :material-file:</span><span class="mdx-badge__text">list[[File](files.md#file) | UUID] | [File](files.md#file) | UUID</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Вложения.

### Ошибки
 - `NotFoundError` - пост не найден.
 - `ValidationError` - ошибка валидации (вероятно из-за большого количества символов).
 - `BannedWordError` - в комментарии есть [запрещенные слова](https://itdsdk.qzz.io/banned-words).
 - `ForbiddenError` - некоторые файлы не принадлежат вам.
 - `RequiresSubscriptionError` - для загрузки видео требуется верификация или подписка ИТД НУКСТА.

## :material-heart: Лайкнуть
```py
comment.like()
```

### Ошибки
 - `NotFoundError` - комментарий не найден.

## :material-heart-off: Убрать лайк
```py
comment.unlike()
```

### Ошибки
 - `NotFoundError` - комментарий не найден.


## :material-delete: Удалить
```python
comment.delete()
```

### Ошибки
 - `NotFoundError` - комментарий не найден.
 - `ForbiddenError` - нету прав на удаление (вы должны быть автором комментария или комментарий должен быть на вашем посте).
 - `AlreadyDeletedError` - комментарий уже удален.
<!-- TOdo добавить в сдк рестор коментов -->

## :material-pencil: Редактировать
```py
edited_at = comment.edit(
    content='123 4'
)
```

### Параметры
#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Новое содержание комментария.

---

# Comments

Список комментариев.

 - [x] has_more
 - [x] total

## Аттрибуты
#### sorting <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[CommentSorting](enums.md#commentsorting)</span></span>
Сортировка комментариев. Можно менять, при смене список автоматически перезагрузится. По умолчанию `CommentSorting.POPULAR`.
```py
comment.sorting = CommentSorting.NEW
```

!!! warning
    Сортировка по дате создания (`CommentSorting.NEW` и `CommentSorting.OLD`) плохо работает на стороне ИТД (посты стоят внезависимотси от выбранной сортировки, может сперва идти более старый а потом новый хотя выбрана сортировка по новым).

## Ошибки при получении
 - `NotFoundError` - пост не найден.
 - `ValidationError` - ошибка валидации (слишком большой лимит).

## :fontawesome-solid-add: Создать
```py
comment = comments.new(
     content='123',
     attachments=[]
)
```

#### content <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Содержание комментария.

#### attachments <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-identifier: | :material-file: || :material-identifier: | :material-file:</span><span class="mdx-badge__text">list[UUID | File] | File | UUID</span></span> <span class="mdx-badge mdx-badge_one_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">One of required</span></span>
Вложения.

### Ошибки
 - `NotFoundError` - пост не найден.
 - `ValidationError` - ошибка валидации (вероятно из-за большого количества символов).
 - `BannedWordError` - в комментарии есть [запрещенные слова](https://itdsdk.qzz.io/banned-words).
 - `ForbiddenError` - некоторые файлы не принадлежат вам.
 - `RequiresSubscriptionError` - для загрузки видео требуется верификация или подписка ИТД НУКСТА.

 ---

# Replies
Список ответов.
 
 - [x] has_more
 - [x] total

## Ошибки при получении
 - `NotFoundError` - комментарий не найден.
 - `ValidationError` - ошибка валидации (слишком большой лимит).
