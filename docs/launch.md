# Запуск

## Способы авторизации
Чтобы получить доступ к аккаунту, потребуется `access` или `refresh` token.

 * `access_token` - JWT токен, действует около 15 минут, обновляется при перезагрузке страницы.
 * `refresh_token` - Случайная строка, действует 7 дней, обнуляется при выходе из аккаунта.


!!! danger
    Никому не передавайте свой `access` или `refresh` токен! С его помощью можно получить полный доступ к аккаунту.

Найти `access token` можно в любом запросе в DevTools (открывается нажатием `F12`) во вкладке `Сеть` / `Network`:
![access token](access-token.png)

Найти `refresh token` можно найти в запросе `/auth/refresh`:
![refresh token](refresh-token.png)


## Запуск клиента

=== "refresh"

    ```python
    from itd import ITDClient

    c = ITDClient('xxx')
    ```

=== "access"

    ```python
    from itd import ITDClient

    c = ITDClient('eyXXX')
    ```

### Логгер
Если вы дополнительно хотите видеть логи itd-sdk, можете добавить вызов `setup_logging` перед инициализацией клиента.
```python
from itd.logger import setup_logging
from itd import ITDClient

setup_logging('INFO')

ITDClient('xxx')
```