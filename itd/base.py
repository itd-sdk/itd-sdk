from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
from functools import wraps

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefinedType

from itd._default import get_default_client

if TYPE_CHECKING:
    from itd.client import Client as ITDClient


def _getattr(self: object, name: str, default: Any | None = None) -> Any:
    try:
        return object.__getattribute__(self, name)
    except AttributeError:
        return default


def _field_has_default(cls: type, name: str) -> bool:
    """Returns True if the field is declared as Field(...) with a default value."""
    for klass in cls.__mro__:
        val = klass.__dict__.get(name)
        if isinstance(val, FieldInfo):
            return not isinstance(val.default, PydanticUndefinedType) or val.default_factory is not None
    return False


class ITDBaseModel:
    _refreshable: bool = True
    _loaded: bool = False
    _loading: bool = False
    _fields_from_data: set[str] = set()
    _validator: Callable[[Any], type[BaseModel]] | None = None # callable (pls use lambda), becuase we havent validator at that moment (it depends on this class)

    def __init__(self, client: ITDClient | None = None) -> None:
        self._client = client or get_default_client()

    def __setattr__(self, name: str, value: Any) -> None:
        if isinstance(value, ITDBaseModel) and (client := _getattr(self, '_client')):
            value._client = client
        object.__setattr__(self, name, value)

    @property
    def client(self) -> ITDClient:
        return self._client

    def _token(self, client: ITDClient | None = None) -> str: # should be property, but it needs client param
        return (client or self._client).token

    def refresh(self) -> Any:
        if self._refreshable:
            raise NotImplementedError(f"{type(self).__name__} must implement refresh()")
        self._loaded = True


    def __getattribute__(self, name: str) -> Any:
        if _getattr(self, '_refreshable'):
            try:
                attr = _getattr(self, name)
            except AttributeError:
                attr = None

            if name.startswith('_') or callable(attr) or name in ('client', 'model_fields_set'):
                return attr

            fields_from_data = _getattr(self, '_fields_from_data', ())
            if not _getattr(self, '_loaded') and (
                (name not in fields_from_data and _field_has_default(type(self), name)) or
                (attr is None and not _field_has_default(type(self), name)) or
                isinstance(attr, FieldInfo)
            ):
                self.refresh()

        return _getattr(self, name)


def refresh_wrapper(func):
    @wraps(func)
    def wrapper(self, client: ITDClient | None = None):
        # if self._loading:
        #     return

        # self._loading = True
        data = func(self, client or self.client)
        if self._validator:
            validated = self._validator().model_validate(data)
            self._fields_from_data = validated.model_fields_set
            for name, value in validated.__dict__.items():
                setattr(self, name, value)

        # self._loading = False
        self._loaded = True

    return wrapper
