from typing import TYPE_CHECKING, Optional, cast

from .api import APIClient
from .object import MWDBObject

if TYPE_CHECKING:
    from .config import MWDBConfig
    from .object import MWDBElementData


class MWDBFile(MWDBObject):
    URL_TYPE = "file"
    TYPE = "file"

    def __init__(self, api: APIClient, data: "MWDBElementData"):
        self._content: Optional[bytes] = None
        super().__init__(api, data)

    @property
    def md5(self) -> str:
        if "md5" not in self.data:
            self._load()
        return cast(str, self.data["md5"])

    @property
    def sha1(self) -> str:
        if "sha1" not in self.data:
            self._load()
        return cast(str, self.data["sha1"])

    @property
    def sha512(self) -> str:
        if "sha512" not in self.data:
            self._load()
        return cast(str, self.data["sha512"])

    @property
    def crc32(self) -> str:
        if "crc32" not in self.data:
            self._load()
        return cast(str, self.data["crc32"])

    @property
    def ssdeep(self) -> str:
        if "ssdeep" not in self.data:
            self._load()
        return cast(str, self.data["ssdeep"])

    @property
    def file_name(self) -> str:
        """
        Sample original name
        """
        if "file_name" not in self.data:
            self._load()
        return cast(str, self.data["file_name"])

    @property
    def file_size(self) -> int:
        """
        Sample size in bytes
        """
        if "file_size" not in self.data:
            self._load()
        return cast(int, self.data["file_size"])

    @property
    def file_type(self) -> str:
        """
        Sample type
        """
        if "file_type" not in self.data:
            self._load()
        return cast(str, self.data["file_type"])

    @property
    def name(self) -> str:
        """
        Alias for :py:attr:`file_name` property
        """
        return self.file_name

    @property
    def size(self) -> int:
        """
        Alias for :py:attr:`file_size` property
        """
        return self.file_size

    @property
    def type(self) -> str:
        """
        Alias for :py:attr:`file_type` property
        """
        return self.file_type

    @property
    def content(self) -> bytes:
        """
        Returns file contents, calling :py:meth:`MWDBFile.download`
        if contents were not loaded yet
        """
        if self._content is None:
            self._content = self.download()
        return self._content

    @property
    def config(self) -> Optional["MWDBConfig"]:
        """
        Returns latest config related with this object

        :rtype: :class:`MWDBConfig` or None
        :return: Latest configuration if found
        """
        from .config import MWDBConfig

        if "latest_config" not in self.data:
            self._load()
        return (
            MWDBConfig(self.api, self.data["latest_config"])
            if self.data["latest_config"] is not None
            else None
        )

    @APIClient.requires("2.2.0")
    def download(self) -> bytes:
        """
        Downloads file contents

        :return: File contents
        :rtype: bytes

        Example - download first file with size less than 1000 bytes and VBS extension

        .. code-block:: python

           dropper = next(
               mwdb.search_files('file.size:[0 TO 1000] AND file.name:"*.vbs"')
           )

           with open(dropper.file_name, "wb") as f:
               f.write(dropper.download())

           print("Downloaded {}".format(dropper.file_name))
        """
        download_endpoint = "file/{id}/download".format(**self.data)
        token = self.api.post(download_endpoint)["token"]
        return cast(
            bytes, self.api.get(download_endpoint, params={"token": token}, raw=True)
        )

    @download.fallback("2.0.0")
    def download_legacy(self) -> bytes:
        token = self.api.post("request/sample/{id}".format(**self.data))["url"].split(
            "/"
        )[-1]
        return cast(bytes, self.api.get("download/{}".format(token), raw=True))
