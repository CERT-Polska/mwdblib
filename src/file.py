from .object import MWDBObject


class MWDBFile(MWDBObject):
    URL_TYPE = "file"
    TYPE = "file"

    def __init__(self, *args, **kwargs):
        self._content = None
        super(MWDBFile, self).__init__(*args, **kwargs)

    @property
    def md5(self):
        if "md5" not in self.data:
            self._load()
        return self.data["md5"]

    @property
    def sha1(self):
        if "sha1" not in self.data:
            self._load()
        return self.data["sha1"]

    @property
    def sha512(self):
        if "sha512" not in self.data:
            self._load()
        return self.data["sha512"]

    @property
    def crc32(self):
        if "crc32" not in self.data:
            self._load()
        return self.data["crc32"]

    @property
    def ssdeep(self):
        if "ssdeep" not in self.data:
            self._load()
        return self.data["ssdeep"]

    @property
    def file_name(self):
        """
        Sample original name
        """
        if "file_name" not in self.data:
            self._load()
        return self.data["file_name"]

    @property
    def file_size(self):
        """
        Sample size in bytes
        """
        if "file_size" not in self.data:
            self._load()
        return self.data["file_size"]

    @property
    def file_type(self):
        """
        Sample type
        """
        if "file_type" not in self.data:
            self._load()
        return self.data["file_type"]

    @property
    def name(self):
        """
        Alias for :py:attr:`file_name` property
        """
        return self.file_name

    @property
    def size(self):
        """
        Alias for :py:attr:`file_size` property
        """
        return self.file_size

    @property
    def type(self):
        """
        Alias for :py:attr:`file_type` property
        """
        return self.file_type

    @property
    def content(self):
        """
        Returns file contents, calling :py:meth:`MWDBFile.download` if contents were not loaded yet
        """
        if self._content is None:
            self._content = self.download()
        return self._content

    @property
    def config(self):
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

    def download(self):
        """
        Downloads file contents

        :return: File contents
        :rtype: bytes

        Example - download first file with size less than 1000 bytes and VBS extension

        .. code-block:: python

           dropper = next(mwdb.search_files('file.size:[0 TO 1000] AND file.name:"*.vbs"'))

           with open(dropper.file_name, "wb") as f:
               f.write(dropper.download())

           print("Downloaded {}".format(dropper.file_name))
        """
        token = self.api.post("request/sample/{id}".format(**self.data))["url"].split("/")[-1]
        return self.api.get("download/{}".format(token), raw=True)


# Backwards compatibility
MalwarecageFile = MWDBFile
