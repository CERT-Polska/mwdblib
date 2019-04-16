from .object import MalwarecageObject, lazy_property


class MalwarecageBlob(MalwarecageObject):
    URL_PATTERN = "blob/{id}"

    @staticmethod
    def create(api, data):
        return MalwarecageBlob(api, data)

    @lazy_property()
    def blob_name(self):
        """
        Blob name
        """
        return self.data.get("blob_name")

    @lazy_property()
    def blob_size(self):
        """
        Blob size in bytes
        """
        return self.data.get("blob_size")

    @lazy_property()
    def blob_type(self):
        """
        Blob semantic type
        """
        return self.data.get("blob_type")

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

    @lazy_property()
    def content(self):
        """
        Contains blob content
        """
        return self.data.get("content")

    @lazy_property()
    def last_seen(self):
        """
        :rtype: datetime.datetime
        :return: datetime object when blob was last seen in Malwarecage
        """
        import dateutil.parser
        return dateutil.parser.parse(self.data["last_seen"]) if "last_seen" in self.data else None
