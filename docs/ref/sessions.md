# :material-cellphone-link: Session
Сессия аккаунта. Отдельно не создается, приходит из [Sessions](#sessions).

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID сессии.

#### is_current <span class="mdx-badge"><span class="mdx-badge__icon">:material-toggle-switch:</span><span class="mdx-badge__text">bool</span></span>
Текущая ли это сессия (та, под которой работает этот клиент).

#### created_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата входа.

#### last_used_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата последнего использования.

#### expires_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата истечения (когда refresh токен перестанет работать).

#### ip <span class="mdx-badge"><span class="mdx-badge__icon">:material-ip:</span><span class="mdx-badge__text">IPv4Address</span></span>
IP-адрес.

#### country <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Код страны по IP. `None`, если не определился.

#### city <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Город по IP. `None`, если не определился.

#### location <span class="mdx-badge"><span class="mdx-badge__icon">:material-map-marker:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Город и страна одной строкой (`Москва, RU`). `None`, если не определилось ни то, ни другое.

#### device_type <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[DeviceType](enums.md#devicetype)</span></span>
Тип устройства.

#### device_os <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Операционная система (`Windows`, `Android` итд).

#### device_os_version <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Версия ОС. `None`, если не определилась.

#### device_model <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Модель устройства. Пока всегда `None`.

#### client_name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Название клиента (берется из `User-Agent`, см. [user_agent](../config.md)). `None` для официального клиента.

#### client_version <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Версия клиента. `None`, если не указана.

## :material-logout: Завершить
```python
session.revoke()
```
или
```python
session.delete()
```

---

# :material-code-brackets: :material-cellphone-link: Sessions
Все сессии аккаунта.

## Получить
```python
sessions = Sessions()
```
Загружает сессии сразу при создании.

## :material-refresh: Перезагрузить
```python
sessions.load()
```

## :material-logout-variant: Завершить все
```python
count = sessions.revoke_all()
```
или
```python
count = sessions.delete_all()
```

Возвращает количество завершенных сессий и очищает список. Текущая сессия тоже завершается.

## Пустой список
```python
sessions = Sessions.empty()
```
Ничего не загружает.
