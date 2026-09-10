# App
## Аттрибуты
#### name <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Название приложения (оно же ключ в словаре).

#### version <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Последняя версия.

#### version_tuple <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :octicons-number-16:</span><span class="mdx-badge__text">tuple[int, ...]</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Версия кортежем (для сравнений типа `app.version_tuple > (2, 8, 0)`).

#### min_version <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Минимальная поддерживаемая версия.

#### min_version_tuple <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :octicons-number-16:</span><span class="mdx-badge__text">tuple[int, ...]</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Минимальная версия кортежем.

#### update_url <span class="mdx-badge"><span class="mdx-badge__icon">:material-link:</span><span class="mdx-badge__text">str</span></span>
Ссылка на обновление.

---

# :material-code-brackets: Apps
Версии официальных клиентов. Ведет себя как словарь, но к приложениям можно обращаться и через точку:

```python
apps = Apps()
apps.android.version
apps['android'].version
```
