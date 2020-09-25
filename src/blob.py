from .object import MWDBObject


class MWDBBlob(MWDBObject):
    URL_TYPE = "blob"
    TYPE = "text_blob"

    @property
    def blob_name(self):
        """
        Blob name
        """
        if "blob_name" not in self.data:
            self._load()
        return self.data["blob_name"]

    @property
    def blob_size(self):
        """
        Blob size in bytes
        """
        if "blob_size" not in self.data:
            self._load()
        return self.data["blob_size"]

    @property
    def blob_type(self):
        """
        Blob semantic type
        """
        if "blob_type" not in self.data:
            self._load()
        return self.data["blob_type"]

    @property
    def name(self):
        """
        Alias for :py:attr:`blob_name` property
        """
        return self.blob_name

    @property
    def size(self):
        """
        Alias for :py:attr:`blob_size` property
        """
        return self.blob_size

    @property
    def type(self):
        """
        Alias for :py:attr:`blob_type` property
        """
        return self.blob_type

    @property
    def content(self):
        """
        Contains blob content

        .. versionchanged:: 3.0.0
           Returned type is guaranteed to be utf8-encoded bytes
        """
        if "content" not in self.data:
            self._load()
        content = self.data["content"]
        if not isinstance(content, bytes):
            content = content.encode("utf-8")
        return content

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
        if self.data["latest_config"] is None:
            return None
        return MWDBConfig(self.api, self.data["latest_config"])

    @property
    def last_seen(self):
        """
        :rtype: datetime.datetime
        :return: datetime object when blob was last seen in MWDB
        """
        import dateutil.parser
        if "last_seen" not in self.data:
            self._load()
        return dateutil.parser.parse(self.data["last_seen"])


# Backwards compatibility
MalwarecageBlob = MWDBBlob
