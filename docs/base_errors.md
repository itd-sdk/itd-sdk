# Основые ошибки
"Код" - код ошибки из JSON ответа сервера. По нему выбирается, какая ошибка должна вызваться.
```json
{"error":{"code":"GIF_REQUIRES_VERIFICATION","message":"GIF-баннер доступен только верифицированным пользователям"}}
#                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                 |           код           |
```

## RateLimitExceeded
Код: `RATE_LIMIT_EXCEEDED`  
Возникает при слишком большом количестве запросов. В сообщении может содержаться время в секундах - сколько надо подождать до разблокировки. Если написано `0` - сервер не указал время.

## InvalidToken
Код: `UNAUTHORIZED`  
Неверный `access_token` (истек либо поврежден). Если указан `refresh token`, SDK подхватит эту ошибку и обновит токен.

## AccountBanned
Код: `ACCOUNT_BANNED` или `USER_BLOCKED`  
Аккаунт заблокирован.

## ProfileRequired
Код: `PROFILE_REQUIRED`  
Требуется профиль (надо пройти начальную страницу `onboarding`, которая открывается при регистрации, где недо заполнить имя и клан).

---


## Ошибки авторизации (при auth запросах)

### InvalidCookie
Неправильные данные cookie. Есть несколько разновидностей:

#### Session not found
Код: `SESSION_NOT_FOUND`  
Сессия не найдена. Скорее всего несуществующий `refresh token`.

#### No refresh token
Код: `REFRESH_TOKEN_MISSING`  
В cookies нету `refresh token`.

#### Session expired
Код: `SESSION_EXPIRED`  
Истек срок годности `refresh token`. Обычно больше месяца после входа.

#### Session revoked
Код: `SESSION_REVOKED`  
`refresh token` пересоздан (revoked). Обычно из-за перезахода (после выхода токен сбрасывается).

### Unauthorized
Код: `UNAUTHORIZED`  
Неавторизован. Скорее всего, какая-то ошибка внутри SDK (cookies не дошли до сервера).