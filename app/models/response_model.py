from typing import Generic, TypeVar

from pydantic import BaseModel


class MessageResponseModel(BaseModel):
    message: str


T = TypeVar('T')


class MessageResponseWithResultModel(BaseModel, Generic[T]):
    message: str
    result: T
