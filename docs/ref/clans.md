# :material-emoticon: Clan
Эмодзи-клан.

## Аттрибуты
#### avatar <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Аватар клана.

#### members_count <span class="mdx-badge"><span class="mdx-badge__icon">:octicons-number-16:</span><span class="mdx-badge__text">int</span></span>
Количество участников.

---

# :material-code-brackets: :material-emoticon: TopClans
Топ кланов.

```python
clans = TopClans()
```
Загружается сразу при создании.


## :material-refresh: Перезагрузить
```python
top_clans.load(limit=10)
```
Очищает список и загружает заново.

## Создать пустой
```python
top_clans = TopClans.empty()
```
