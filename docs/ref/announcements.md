# :material-bullhorn: Announcement
Анонс - плашка, которую ИТД показывает в официальном клиенте (обновление, новость итд).

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">str</span></span>
ID анонса (не UUID, а строка типа `new-feed-2026-06-15`).

#### title <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Заголовок.

#### description <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Описание. `None`, если не установлено.

#### additional_text <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Дополнительный текст под описанием. `None`, если не установлено.

#### image <span class="mdx-badge"><span class="mdx-badge__icon">:material-image:</span><span class="mdx-badge__text">[AnnouncementImage](#announcementimage)</span></span>
Картинка анонса. `None`, если картинки нет.

#### buttons <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-gesture-tap-button:</span><span class="mdx-badge__text">list[[AnnouncementButton](#announcementbutton)]</span></span>
Кнопки анонса.

## :material-eye: Отметить прочитанным
```python
announcement.read()
```
Запоминает ID в файле сессии, чтобы [Announcements](#announcements) больше его не показывали. В API ничего не уходит - это чисто локально, поэтому нужен клиент, созданный через [from_file](client.md) (иначе `AssertionError`).

---

# :material-image: AnnouncementImage
Картинка анонса.

## Аттрибуты
#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Ссылка на изображение.

#### width <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Ширина изображения (может быть `None`).

#### height <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Высота изображения (может быть `None`).

---

# :material-gesture-tap-button: AnnouncementButton
Кнопка анонса.

## Аттрибуты
#### title <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Текст кнопки.

#### style <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AnnouncementButtonStyle](enums.md#announcementbuttonstyle)</span></span>
Стиль кнопки.

#### action <span class="mdx-badge"><span class="mdx-badge__icon">:material-gesture-tap:</span><span class="mdx-badge__text">[AnnouncementButtonAction](#announcementbuttonaction)</span></span>
Действие при нажатии.

---

# :material-gesture-tap-button: AnnouncementButtonAction
Действие при нажатии на кнопку.

## Аттрибуты
#### type <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[AnnouncementButtonType](enums.md#announcementbuttontype)</span></span>
Тип действия при нажатии.

#### url <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Ссылка, на которую редиректить после нажатия. `None`, если [тип](#type-announcementbuttontype) не `LINK`.

---

# :material-code-brackets: :material-bullhorn: Announcements
Список анонсов.

## Получить
```python
announcements = Announcements()
```

### Параметры
#### hide_seen <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Убирать ли анонсы, которые уже отметили через [read()](#announcement). По умолчанию `True`. Работает только с клиентом из файла сессии.

## Первый анонс
```python
announcement = Announcements().get()
```
Возвращает первый анонс или `None`, если анонсов нет.

## :material-refresh: Перезагрузить
```python
announcements.load(hide_seen=True)
```

## Пустой список
```python
announcements = Announcements.empty()
```
