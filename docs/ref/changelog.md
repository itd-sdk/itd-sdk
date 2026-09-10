# Version

## Аттрибуты
#### version <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Версия.

#### changes <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :material-text:</span><span class="mdx-badge__text">list[str]</span></span>
Список изменений.

#### date_str <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Дата так, как ее отдает ИТД (`13 мая`).

#### date <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">date</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Разобранная дата. Для получения `date`:

```
uv add itd-sdk[date]
```

#### version_tuple <span class="mdx-badge"><span class="mdx-badge__icon">:material-code-brackets: :octicons-number-16:</span><span class="mdx-badge__text">tuple[int, ...]</span></span> <span class="mdx-badge mdx-badge_alias"><span class="mdx-badge__icon">property</span></span>
Версия кортежем.

---

# :material-format-list-bulleted: Changelog
Список изменений официального веб клиента.

```py
changelog = Changelog()
changelog[0].changes
```
