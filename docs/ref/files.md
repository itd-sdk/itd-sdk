# :material-file: File
Загруженный файл. Загружается отдельно, а потом прикрепляется к посту или комментарию (в `attachments`).

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID файла. Именно его надо передавать в `attachments` (или сам объект).

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-link:</span><span class="mdx-badge__text">str</span></span>
Ссылка на файл.

#### filename <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Имя файла, под которым он был загружен.

#### mime_type <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
MIME-тип (`image/png`, `video/mp4` итд).

#### size <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Размер в байтах.


## :material-upload: Загрузка
```python
file = File.from_path('picture.png')
```

### Параметры
#### path <span class="mdx-badge"><span class="mdx-badge__icon">:material-folder:</span><span class="mdx-badge__text">Path | str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Путь до файла. Имя берется из него же.

### :material-memory: Из байтов
```python
file = File.from_bytes(data, 'picture.png')
```

#### data <span class="mdx-badge"><span class="mdx-badge__icon">:material-file:</span><span class="mdx-badge__text">bytes | BufferedReader</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Содержимое файла.

#### name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Имя файла. Если не указать, тип определится по содержимому, для этого нужен `filetype`:

```
uv add itd-sdk[filetype]
```

Без него будет `ImportError`. Если тип определить не удалось, файл загрузится как `file.0`.

## :material-download: Скачать
```python
file.download('picture.png')
```

#### name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Куда сохранить. По умолчанию - [filename](#filename-str).

## :material-delete: Удалить
```python
file.delete()
```

## Ошибки при загрузке
 - `UploadError` - файл не загрузился.
 - `ModerationFailedError` - файл не прошел модерацию.
 - `InvalidFileTypeError` - недопустимый тип файла.
 - `TooLargeError` - файл слишком большой.

---

# :material-image: PostAttach
Вложение поста (из [post.attachments](posts.md#attachments-listpostattach)). Отдельно не создается.

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID вложения.

#### type <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AttachType](enums.md#attachtype)</span></span>
Тип вложения.

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-link:</span><span class="mdx-badge__text">str</span></span>
Ссылка на вложение.

#### thumbnail_url <span class="mdx-badge"><span class="mdx-badge__icon">:material-link:</span><span class="mdx-badge__text">str</span></span>
Ссылка на превью. Всегда `None`.

#### width <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Ширина. `None` для аудио.

#### height <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Высота. `None` для аудио.

#### extension <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Расширение по типу вложения: `jpg`, `mp4` или `mp3`.

## :material-download: Скачать
```python
attach.download('picture.jpg')
```

#### name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Куда сохранить. У вложения поста нет своего имени, поэтому его надо указать.

## :material-image-search: Записать открытие фото
```python
attach.record_open()
```

Событие уходит в [dwell](../features.md), как в официальном клиенте при открытии фото на весь экран. Только для `AttachType.IMAGE`.

## :material-play: Записать просмотр видео
```python
attach.record_progress(duration=30000, played=12000)
```

#### duration <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Общая длина видео в миллисекундах. ИТД ее не отдает, так что считайте сами.

#### played <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Сколько просмотрено (мс). По умолчанию - все видео целиком.

Только для `AttachType.VIDEO`.

---

# :material-image: CommentAttach
Вложение комментария (и) [comment.attachments](comments.md#attachments-listcommentattach)). Наследует [PostAttach](#postattach), но у него есть имя и размер. События просмотра записывать нельзя - `record_open` и `record_progress` выбрасывают `AttributeError`.

## Аттрибуты
Все из [PostAttach](#postattach), плюс:

#### filename <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Имя файла, под которым он был загружен.

#### mime_type <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
MIME-тип.

#### size <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Размер в байтах.

#### duration <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Длительность (для аудио и видео). `None` для картинок.

#### order <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Порядок вложения в комментарии.

## :material-download: Скачать
```python
attach.download()
```

#### name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Куда сохранить. По умолчанию - [filename](#filename-str_1).
