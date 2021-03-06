from .object import MWDBObject
from .config import MWDBConfig
from typing import Any, Optional


class MWDBFile(MWDBObject):
    URL_TYPE: str = ...
    TYPE: str = ...
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    @property
    def md5(self) -> str: ...
    @property
    def sha1(self) -> str: ...
    @property
    def sha512(self) -> str: ...
    @property
    def crc32(self) -> str: ...
    @property
    def ssdeep(self) -> str: ...
    @property
    def file_name(self) -> str: ...
    @property
    def file_size(self) -> int: ...
    @property
    def file_type(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def size(self) -> int: ...
    @property
    def type(self) -> str: ...
    @property
    def content(self) -> bytes: ...
    @property
    def config(self) -> Optional[MWDBConfig]: ...
    def download(self) -> bytes: ...


MalwarecageFile = MWDBFile
