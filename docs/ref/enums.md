# Enums

### DebugResponseMode
Режим показа ответов сервера.

 - `DebugResponseMode.NO`: Не показывать ответ.
 - `DebugResponseMode.BEFORE`: Показывать ответ до обработки (сырой).
 - `DebugResponseMode.AFTER`: Показывать ответ после обработки (если при обработке возникла ошибка, ответ не выведется).
 - `DebugResponseMode.KEYS`: Показывать только ключи ответа (после обработки).

### ParseMode
 Режим парсинга.
 
 - `ParseMode.NO`: Выключить парсинг.
 - `ParseMode.MARKDOWN`: Markdown парсинг.
 - `ParseMode.HTML`: HTML парсинг.

### AuthLevel
Уровень авторизации.

 - `AuthLevel.NO`: Без авторизации.
 - `AuthLevel.ACCESS`: access токен.
 - `AuthLevel.REFRESH`: refresh токен.

### PostsTab
Вкладка постов.

 - `PostsTab.POPULAR`: Обычная лента постов.
 - `PostsTab.FOLLOWING`: Лента постов от авторов, на которых вы подписаны.
 - `PostsTab.CLAN`: Лента постов от авторов, у которых одинаковый с вами клан.

### UserPostSorting
Режим сортировки постов пользователя.

 - `UserPostSorting.NEW`: Сортировка постов по дате создания.
 - `UserPostSorting.POPULAR`: Сортировка постов по количеству лайков.

### AccessType
Уровень доступа.

 - `AccessType.NOBODY`: Никто.
 - `AccessType.MUTUAL`: Взаимные подписки (вы подписаны на пользователя и он подписан на вас).
 - `AccessType.FOLLOWERS`: Подписчики.
 - `AccessType.EVERYONE`: Все.

### ReportTargetType
Тип объекта, на который жалуетесь.

 - `ReportTargetType.POST`: Пост.
 - `ReportTargetType.USER`: Пользователь.
 - `ReportTargetType.COMMENT`: Комментарий.

### ReportReason
Причина жалобы.

 - `ReportReason.SPAM`: Спам или нежелательный контент.
 - `ReportReason.VIOLENCE`: Насилие или опасные действия.
 - `ReportReason.HATE`: Ненависть или травля.
 - `ReportReason.ADULT`: Контент для взрослых (18+).
 - `ReportReason.FRAUD`: Дезинформация или обман.
 - `ReportReason.OTHER`: Другое.

### Role
Роль пользователя.

 - `Role.USER`: Обычный пользователь.
 - `Role.ADMIN`: Администратор.

### SpanType
Тип спана.

 - `SpanType.MONOSPACE`: `Моноширный` (код).
 - `SpanType.STRIKE`: ~~Зачеркнутый~~.
 - `SpanType.BOLD`: **Жирный**.
 - `SpanType.ITALIC`: *Курсив*.
 - `SpanType.UNDERLINE`: <u>Подчеркнутый</u>.
 - `SpanType.HASHTAG`: Хэштэг. Заполняется самим ИТД при создании поста.
 - `SpanType.LINK`: Ссылка. При создании надо указать `url`.
 - ~~`SpanType.QUOTE`: <q>Цитата</q>.~~
 - `SpanType.MENTION`: Упоминание. ~~Заполняется~~ Должно заполняться самим ИТД при создании поста. <!-- так вроде же заполняется -->

!!! warning
    Цитаты (`SpanType.QUOTE`) не добавлены на бэкенд (есть только на клиенте).

### LastSeenUnit
Юнит времени.

 - `LastSeenUnit.JUST_NOW`: Только что.
 - `LastSeenUnit.RECENTLY`: Недавно.
 - `LastSeenUnit.MINUTES`: {} минут назад.
 - `LastSeenUnit.HOURS`: {} часов назад.
 - `LastSeenUnit.THIS_WEEK`: На этой неделе.
 - `LastSeenUnit.THIS_MONTH`: В этом месяце.
 - `LastSeenUnit.LONG_AGO`: Давно.


### NotificationType
Тип уведолмения.

 - `NotifcationType.LIKE`: Лайк поста.
 - `NotifcationType.COMMENT`: Комментарий под постом.
 - `NotifcationType.REPLY`: Ответ на комментарий.
 - `NotifcationType.REPOST`: Репост поста.
 - ~~`NotifcationType.MENTION`: Упоминание в посте.~~
 - `NotifcationType.FOLLOW`: Подписка.
 - ~~`NotifcationType.FOLLOW_REQUEST`: Запроса на подписку.~~
 - ~~`NotifcationType.FOLLOW_ACCEPTED`: Одобрение запроса на подписку.~~
 - ~~`NotifcationType.COMMENT_LIKE`: Лайк комментария.~~
 - ~~`NotifcationType.COMMENT_MENTION`: Упоминание в комментарии.~~
 - `NotifcationType.WALL_POST`: Пост на стене.

!!! warning
    Упоминания, лайки комментариев и запросы на подписку (`NotifcationType.MENTION`, `NotifcationType.FOLLOW_REQUEST`, `NotifcationType.FOLLOW_ACCEPTED`, `NotifcationType.COMMENT_LIKE`, `NotifcationType.COMMENT_MENTION`) не добавлены на бэкенд (есть только на клиенте).

### NotificationTargetType
Тип цели уведомления.

 - `NotificationTargetType.POST`: Пост.

!!! question "Предположение"
    Возможно в будущем появится и `COMMENT` (для лайков и упоминаний в комментариях).

!!! note
    Если цель - пользователь (например при подписке), значение будет `None`.

### NotificationSubjectType
Тип объекта, о котором уведомление.

 - `NotificationSubjectType.COMMENT`: Комментарий.
 - `NotificationSubjectType.POST`: Пост.

### CommentSorting
Сортировка комментариев.

 - `CommentSorting.NEW`: Сперва новые.
 - `CommentSorting.POPULAR`: Сперва популярные (по колву лайков и ответов).
 - `CommentSorting.OLD`: Сперва сатрые.

!!! warning
    Сортировка по дате создания (`CommentSorting.NEW` и `CommentSorting.OLD`) плохо работает на стороне ИТД.

### UserAgent
User-Agent заголовок.

 - `UserAgent.BROWSER`: Браузерный агент (`Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0`).
 - `UserAgent.SDK`: Агент SDK (`itd-sdk/{} (Python/{})`).
 - `UserAgent.DEFAULT`: Дефолтный агент от `requests`.
 - `UserAgent.EMPTY`: Пустой.

### AttachType
Тип вложения.

 - `AttachType.IMAGE`: Картинка.
 - `AttachType.VIDEO`: Видео.
 - `AttachType.AUDIO`: Аудио.
 - `AttachType.MEDIA`: Медиа (картинка или видео).

### DeviceType
Тип устройства в [сессии](sessions.md#session).

 - `DeviceType.DESKTOP`: Компьютер.
 - `DeviceType.MOBILE`: Телефон.

### ViewSource
Откуда пост попал в поле зрения - уходит в статистику просмотров (см. [dwell](../features.md)).

 - `ViewSource.FEED_GLOBAL`: Общая лента.
 - `ViewSource.FEED_FOLLOWING`: Лента подписок.
 - `ViewSource.FEED_CLAN`: Лента клана.
 - `ViewSource.PROFILE`: Профиль.
 - `ViewSource.HASHTAG`: Страница хэштэга.
 - `ViewSource.POST_PAGE`: Страница поста.
 - `ViewSource.LINK`: Переход по ссылке.
 - `ViewSource.SEARCH`: Поиск.

### ViewReason
Почему просмотр закончился.

 - `ViewReason.NORMAL`: Пост просто ушел из зоны видимости.
 - `ViewReason.BLUR`: Страница потеряла фокус.
 - `ViewReason.HIDDEN`: Вкладка скрыта.
 - `ViewReason.PAGE_HIDE`: Страница закрывается.
 - `ViewReason.UNOBSERVE`: Пост удален из DOM.
 - `ViewReason.INACTIVE`: Пользователь перестал что-либо делать (см. [dwell_inactive_timeout](../config.md)).

### InteractionType
Тип взаимодействия с вложением.

 - `InteractionType.PHOTO_OPEN`: Открытие фото.
 - `InteractionType.VIDEO_PROGRESS`: Просмотр видео.

### LoadStatus
Насколько загружена модель.

 - `LoadStatus.NO`: Данных нет, было только создание.
 - `LoadStatus.LOADING`: Данные загружаются прямо сейчас.
 - `LoadStatus.PARTIALLY`: Часть данных есть (модель пришла в списке или вложенной в другую).
 - `LoadStatus.FULL`: Загружена целиком.

### AnnouncementButtonStyle
Стиль кнопки [анонса](announcements.md#announcementbutton).

 - `AnnouncementButtonStyle.PRIMARY`: Основная кнопка.
 - `AnnouncementButtonStyle.SECONDARY`: Второстепенная.

### AnnouncementButtonType
Тип кнопки [анонса](announcements.md#announcementbutton).

 - `AnnouncementButtonType.DISMISS`: Закрыть анонс.
 - `AnnouncementButtonType.LINK`: Открыть ссылку (`action.url`).
