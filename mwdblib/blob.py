import datetime
from typing import TYPE_CHECKING, Optional, cast

from .object import MWDBObject

if TYPE_CHECKING:
    from .config import MWDBConfig


class MWDBBlob(MWDBObject):
    URL_TYPE: str = "blob"
    TYPE: str = "text_blob"

    @property
    def blob_name(self) -> str:
        """
        Blob name
        """
        if "blob_name" not in self.data:
            self._load()
        return cast(str, self.data["blob_name"])

    @property
    def blob_size(self) -> int:
        """
        Blob size in bytes
        """
        if "blob_size" not in self.data:
            self._load()
        return cast(int, self.data["blob_size"])

    @property
    def blob_type(self) -> str:
        """
        Blob semantic type
        """
        if "blob_type" not in self.data:
            self._load()
        return cast(str, self.data["blob_type"])

    @property
    def name(self) -> str:
        """
        Alias for :py:attr:`blob_name` property
        """
        return self.blob_name

    @property
    def size(self) -> int:
        """
        Alias for :py:attr:`blob_size` property
        """
        return self.blob_size

    @property
    def type(self) -> str:
        """
        Alias for :py:attr:`blob_type` property
        """
        return self.blob_type

    @property
    def content(self) -> bytes:
        """
        Contains blob content

        .. versionchanged:: 3.0.0
           Returned type is guaranteed to be utf8-encoded bytes
        """
        if "content" not in self.data:
            self._load()
        content = cast(str, self.data["content"])
        return content.encode("utf-8")

    @property
    def config(self) -> Optional["MWDBConfig"]:
        """
        Returns latest config related with this object

        :return: Latest configuration if found
        """
        from .config import MWDBConfig

        if "latest_config" not in self.data:
            self._load()
        if self.data["latest_config"] is None:
            return None
        return MWDBConfig(self.api, self.data["latest_config"])

    @property
    def last_seen(self) -> "datetime.datetime":
        """
        :return: datetime object when blob was last seen in MWDB
        """
        if "last_seen" not in self.data:
            self._load()
        return datetime.datetime.fromisoformat(self.data["last_seen"])
