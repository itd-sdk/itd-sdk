# :material-flag: Report
Жалоба. Обычно создается не напрямую, а через объект, на который жалуетесь - [post.report()](posts.md), [comment.report()](comments.md) или [user.report()](users.md).

## Аттрибуты
#### id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span>
ID жалобы.

#### created_at <span class="mdx-badge"><span class="mdx-badge__icon">:material-calendar:</span><span class="mdx-badge__text">datetime</span></span>
Дата отправки.

#### target_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> 
ID объекта, на который жалуетесь.

#### target_type <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[ReportTargetType](enums.md#reporttargettype)</span></span> 
Тип объекта.

#### reason <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[ReportReason](enums.md#reportreason)</span></span> 
Причина жалобы.

#### description <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Описание жалобы.


## Создать
```python
report = Report(
    target_id=post.id,
    target_type=ReportTargetType.POST,
    reason=ReportReason.SPAM,
    description='какашка блин ванючая ваще плохо себя ведет'
)
```

### Параметры
#### target_id <span class="mdx-badge"><span class="mdx-badge__icon">:material-identifier:</span><span class="mdx-badge__text">UUID</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
ID объекта, на который жалуетесь.

#### target_type <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[ReportTargetType](enums.md#reporttargettype)</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Тип объекта.

#### reason <span class="mdx-badge"><span class="mdx-badge__icon">:material-form-select:</span><span class="mdx-badge__text">[ReportReason](enums.md#reportreason)</span></span> <span class="mdx-badge mdx-badge_required"><span class="mdx-badge__icon">:material-information:</span><span class="mdx-badge__text">Required</span></span>
Причина жалобы.

#### description <span class="mdx-badge"><span class="mdx-badge__icon">:material-text:</span><span class="mdx-badge__text">str</span></span>
Описание. По умолчанию пустое.

## Ошибки
 - `AlreadyReportedError` - вы уже жаловались на этот объект.
 - `NotFoundError` - объекта не существует.
 - `ValidationError` - ошибка валидации.
