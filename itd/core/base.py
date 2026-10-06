from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from functools import cache, cached_property
from typing import TYPE_CHECKING, Annotated, Any, Iterator, Literal, SupportsIndex, TypeVar, cast, overload
from uuid import UUID

from pydantic import BaseModel, BeforeValidator
from pydantic.fields import FieldInfo
from pydantic_core.core_schema import with_info_plain_validator_function

from itd.core.default import get_default_client
from itd.core.logger import get_logger
from itd.core.utils import parse_datetime
from itd.enums import ALL, BATCH, All, Batch, LoadStatus

if TYPE_CHECKING:
    from itd.core.client import Client


l = get_logger('base')  # noqa: E741 # seriously, whats wrong that i am using "l" for logger? not willing to use full "logger", so, shut up


@cache
def get_pydantic_model(cls: type) -> type[BaseModel]:
    """Класс-валидатор модели: собирается один раз на модель при первой валидации"""
    # __module__ for correct forward refs in annotations
    return type(f'_{cls.__name__}Validate', (BaseModel, cls), {'__module__': cls.__module__})


def _getattr(self: object, name: str, default: Any | None = None) -> Any:
    try:
        return object.__getattribute__(self, name)
    except AttributeError:
        return default


class ITDBaseModel:
    """Базовый класс модельки"""

    _refreshable: bool = True
    load_status: LoadStatus = LoadStatus.NO
    _load_with_parent: bool = True  # load parent model if model called

    def __init__(self, client: Client | None = None) -> None:
        self._client = client or get_default_client()

        if '_loaded_attrs' not in self.__dict__:  # model could set attributes before calling super().__init__() (eg User sets username)
            self._loaded_attrs: set[str] = set()
        self._extra_context = {}

    def _init_refresh(self):
        if self.client.config.load_on_init and self._refreshable:
            self.refresh()

    def __setattr__(self, name: str, value: Any) -> None:
        # клиент раздается только настоящим полям (post.author = user), но не обратным ссылкам:
        # comment._post = post отдал бы клиента комментария посту, а не наоборот
        if not name.startswith('_') and isinstance(value, ITDBaseModel) and (client := _getattr(self, '_client')):  # ai
            value._client = client
        if '_loaded_attrs' not in self.__dict__:  # attribute is set before __init__, remember it anyway - otherwise getattr will refresh loaded value
            object.__setattr__(self, '_loaded_attrs', set())
        self._loaded_attrs.add(name)
        object.__setattr__(self, name, value)

    def _post_refresh(self, context: dict = {}): ...

    def is_loaded(self, name: str) -> bool:  # claudes idea
        """Пришло ли поле в данных

        Не трогает API, в отличие от обычного обращения к полю: `post.is_loaded('first_comments')` вместо `post.first_comments`,
        когда надо просто узнать, есть ли значение (в списках приходит не все, что есть в одиночном ответе).

        Args:
            name (str): Имя поля

        Returns:
            bool: Загружено ли поле
        """
        return name in self._loaded_attrs

    @property
    def client(self) -> Client:
        return self._client

    def _refresh(self, *, client: Client) -> dict:
        raise NotImplementedError()

    def refresh(self, *, client: Client | None = None) -> Any:
        if not self._refreshable:
            l.warning(f'{self.__class__.__name__} is not refreshable but refresh is called')
        self.load_status = LoadStatus.LOADING
        context = {'client': client or self.client}
        context.update(self._extra_context)
        self._fill_from_data(self._refresh(client=client or self.client), context=context)
        self.load_status = LoadStatus.FULL
        return self

    def _fill_from_data(self, data: dict, *, context: dict | None = None):
        assert self._pydantic_model, 'Unable to use fill_from_data without a validator'
        context = dict(context or {})
        context.update(self._extra_context)
        model = self._pydantic_model.model_validate(data, context=context)  # вложенные модели строятся с клиентом родителя
        self._loaded_attrs = model.model_fields_set  # значения автоматом добавляются через setattr # так значит это же тогда надо закоментить? # хз наверн
        for name, value in model.__dict__.items():
            object.__setattr__(self, name, value)

        self._post_refresh(context=context)

    @classmethod
    def from_dict(cls, data: dict, *, context: dict | None = None, client: Client | None = None):
        context = dict(context or {})
        instance = cls.__new__(cls)
        ITDBaseModel.__init__(instance, client or context.get('client'))  # клиент из контекста - так вложенные модели попадают к клиенту родителя

        context.setdefault('client', instance.client)
        instance._fill_from_data(data, context=context)
        if instance.load_status == LoadStatus.NO:
            instance.load_status = LoadStatus.PARTIALLY
        return instance

    def to_dict(self, *, mode: Literal['python', 'json'] = 'python', by_alias: bool = False):
        model = self._pydantic_model.model_validate(self, from_attributes=True, by_alias=False, by_name=True)
        # for name, value in model.__dict__.items():
        #     object.__setattr__(model, name, value)
        return {
            k: v.to_dict() if isinstance(v, ITDBaseModel) else v for k, v in model.model_dump(exclude={'load_status'}, mode=mode, by_alias=by_alias).items()
        }

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        if issubclass(source, BaseModel):
            return handler(source)
        # build like just  simple from_dict
        return with_info_plain_validator_function(
            lambda data, info: data if isinstance(data, source) else source.from_dict(data, context=dict(info.context or {}))
        )

    # def __pydantic_serializer__

    @property
    def _pydantic_model(self) -> type[BaseModel]:
        return get_pydantic_model(type(self))  # один класс на модель, а не на объект

    if not TYPE_CHECKING:

        def __getattribute__(self, name: str) -> Any:
            try:
                value = object.__getattribute__(self, name)
                exc = None
            except AttributeError as e:
                value = None
                exc = e

            if (
                _getattr(self, '_refreshable')
                and not name.startswith('_')
                and name not in ('client', 'model_fields_set', 'load_status')
                and not callable(value)
                and not isinstance(_getattr(type(self), name), property | cached_property)
                and _getattr(self, 'load_status') in (LoadStatus.NO, LoadStatus.PARTIALLY)
                and name not in (_getattr(self, '_loaded_attrs') or {name})
                and self.client.config.load_on_getattr
                and not (isinstance(value, ITDBaseModel) and not value._load_with_parent)
            ):
                l.info('refresh %s field=%s load_status=%s', self.__class__.__name__, name, _getattr(self, 'load_status').value)
                self.refresh()
                return object.__getattribute__(self, name)

            annotations = {}
            [annotations.update(_getattr(c, '__annotations__')) for c in _getattr(self, '__class__').__mro__ if _getattr(c, '__annotations__')]

            if isinstance(value, FieldInfo) or (not name.startswith('_') and exc is not None and not _getattr(self, 'client').config.load_on_getattr):
                value_type = annotations[name]
                if 'None' in value_type:
                    l.warning('returned fake value None for %s: please load data (call refresh()) before get attributes', name)
                    return None
                elif value_type == 'int':
                    l.warning('returned fake value 0 for %s: please load data (call refresh()) before get attributes', name)
                    return 0
                elif value_type == 'UUID':
                    l.warning('returned fake value 00000000-0000-0000-0000-000000000010 for %s: please load data (call refresh()) before get attributes', name)
                    return UUID('00000000-0000-0000-0000-000000000000')
                elif value_type == 'str':
                    l.warning('returned fake value "" for %s: please load data (call refresh()) before get attributes', name)
                    return ''
                elif value_type == 'bool':
                    l.warning('returned fake value False for %s: please load data (call refresh()) before get attributes', name)
                    return False  # дилема
                l.error('cannot fake data for %s (type %s): please load data (call refresh()) before get attributes', name, value_type)
                raise RuntimeError(f'cannot fake data for {name} (type {value_type}): please load data (call refresh()) before get attributes')

            if exc is not None:
                raise exc
            return value


T = TypeVar('T', bound=ITDBaseModel)


class ITDList(ITDBaseModel, list[T]):
    """Базовый класс списка"""

    _get_total = None
    _refreshable = False
    has_more = True
    idx = 0
    _is_page_pagination: bool = False
    cursor = None

    def _fetch(self, client: Client, limit: int) -> dict:
        return {}

    # edited by calude, thats so fucking crazy pagination
    def load(self, count: int | All | Batch = BATCH, limit: int | Batch = BATCH, client: Client | None = None) -> list[T]:
        """Загрузить объекты

        Args:
            count (int | All | Batch, optional): Количество объектов. Defaults to BATCH.
            limit (int | Batch, optional): Лимит. Defaults to BATCH.
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            list[T]: Новые объекты
        """
        if not (self.has_more or (client or self.client).config.force_load_lists):
            l.warning('skip load because has_more=False')
            return []

        default_limit = (client or self.client).config.batch_sizes._values[self.__class__.__name__.lower()]
        limit = limit or default_limit
        if isinstance(count, int) and count < limit:
            limit = count

        if self._is_page_pagination and limit != default_limit:
            l.warning('unable to change limit in %s (page pagination), using default %s', self.__class__.__name__.lower(), default_limit)
            count = limit = default_limit

        l.debug('load %s count=%s limit=%s cursor=%s', self.__class__.__name__.lower(), count, limit, self.cursor)

        # Batch = load one batch (limit), All = load everything, int = load exactly N
        left = None if isinstance(count, All) else (count or limit)
        added = []

        while left is None or left > 0:
            batch = limit if left is None else min(limit, left)
            data = self._fetch(client or self.client, batch)
            objects = self._get_objects(data)
            self.has_more = self._get_has_more(data)
            if self._get_cursor(data) is not None:
                self.cursor = self._get_cursor(data)

            if self._get_total:
                self.total = self._get_total(data)
                if getattr(self, '_min_total', None) and self._min_total > self.total:
                    raise IndexError(f'Given index ({self._min_total - 1}) is too high. Total items is {self.total}')

            length = len(objects)
            if objects and (client or self.client).config.userposts_add_pinned_post and length == batch + 1:  # skip pinned post
                length -= 1

            if left is not None:
                left -= length

            l.info('fetched %s %s (was %s) cursor=%s has_more=%s', length, self.__class__.__name__.lower(), len(self), self.cursor, self.has_more)
            models = self._to_models(objects, client or self.client)
            self.extend(models)
            added.extend(models)

            if not self.has_more or not objects:
                break

        return added

    @abstractmethod
    def _to_models(self, objects: list, client: Client) -> list[T]: ...

    @staticmethod
    def _get_has_more(data: dict) -> bool:
        return True

    @staticmethod
    def _get_cursor(data: dict):
        return 0

    @staticmethod
    def _get_objects(data: dict) -> list[dict]:
        return []

    def refresh(self, count: int | All | Batch | None = None, limit: int | Batch = BATCH, *, client: Client | None = None) -> list[T]:
        """Обновить список (удалить все элементы и загрузить заново)

        Args:
            count (int | All | Batch, optional): Количество объектов (None - количество на данный момент). Defaults to None.
            limit (int | Batch, optional): Лимит. Defaults to BATCH.
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            list[T]: Обновленный список
        """
        if count is None:
            count = len(self)
            if self and getattr(self[0], 'is_pinned', False):  # skip pinned post
                count -= 1
        self.clear()
        self.cursor = None
        self.has_more = True  # also refresh has_more
        l.debug('refresh %s count=%s limit=%s', self.__class__.__name__.lower(), str(count), limit)
        return self.load(count, limit, client)

    def load_all(self, limit: int | Batch = BATCH, client: Client | None = None) -> list[T]:
        """Загрузить все объекты (эквивалент self.load(ALL))

        Args:
            limit (int | Batch, optional): Лимит. Defaults to BATCH.
            client (Client | None, optional): Клиент. Defaults to None.

        Returns:
            list[T]: Список
        """
        return self.load(ALL, limit, client)

    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> list[T]: ...

    def __getitem__(self, index: SupportsIndex | slice) -> T | list[T]:
        if isinstance(index, slice):
            value: int | None = index.stop
        else:
            value = cast(int, index)

        if ((value is not None and value > len(self) - 1) or value is None) and self.client.config.load_on_getitem is not None:
            if value:
                self._min_total = value + 1

            if value is None or isinstance(self.client.config.load_on_getitem, All):
                l.debug('getitem load all')
                self.load_all()
            elif self._is_page_pagination or isinstance(self.client.config.load_on_getitem, Batch):
                l.debug('getitem load batch')
                self.load(BATCH)
            else:
                l.debug('getitem load %s', value - len(self) + self.client.config.load_on_getitem)
                self.load(value - len(self) + self.client.config.load_on_getitem)

        return super().__getitem__(index)

    def __next__(self) -> T:
        assert self.client.config.load_on_iter is not None
        if getattr(self, 'total', None) and self.idx >= self.total:
            raise StopIteration()
        if self.idx >= len(self) and (self.has_more or self.client.config.force_load_lists):
            l.debug('not enough items to call next, load')
            self.load(self.client.config.load_on_iter)
        if self.idx >= len(self):
            raise StopIteration()
        item = self[self.idx]
        self.idx += 1
        return item

    def __iter__(self) -> Iterator[T]:
        if self.client.config.load_on_iter is None:
            return super().__iter__()
        self.idx = 0
        return self

    @property
    def all(self) -> list[T]:
        return self.load_all()

    def clear(self):
        super().clear()
        self.cursor = None
        self.has_more = True


ITDdatetime = Annotated[datetime, BeforeValidator(parse_datetime)]
