# Авторизация
Для выполнения любой из команд, связанных с авторизацией, нужен `refresh` токен.

## Изменить пароль
```python
c.change_password(
    old='12345678',
    new='12345679'
)
```
!!! danger

    После сброса пароля `refresh token` может сбросится. Нужно входить заново.

### Параметры

#### old <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Старый пароль.

#### new <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Новый пароль.

### Ошибки
 - `SamePassword` - пароли повторяются.
 - `InvalidOldPassword` - старый пароль неверный.

## Выйти
```python
c.logout()
```

!!! danger

    После выхода `refresh token` сбросится. Нужно входить заново.


## Обновить `access_token`
```python
token = c.refresh_auth()
```
