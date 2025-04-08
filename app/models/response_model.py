from typing import Generic, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel


class MessageResponseModel(BaseModel):
    message: str


T = TypeVar('T')


class MessageResponseWithResultModel(GenericModel, Generic[T]):
    message: str
    result: T
