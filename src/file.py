import warnings

from .object import MalwarecageObject, lazy_property


class MalwarecageFile(MalwarecageObject):
    URL_PATTERN = "file/{id}"

    @staticmethod
    def create(api, data):
        return MalwarecageFile(api, data)

    @lazy_property()
    def md5(self):
        return self.data.get("md5")

    @lazy_property()
    def sha1(self):
        return self.data.get("sha1")

    @lazy_property()
    def sha512(self):
        return self.data.get("sha512")

    @lazy_property()
    def crc32(self):
        return self.data.get("crc32")

    @lazy_property()
    def ssdeep(self):
        return self.data.get("ssdeep")

    @lazy_property()
    def file_name(self):
        """
        Sample original name
        """
        return self.data.get("file_name")

    @lazy_property()
    def file_size(self):
        """
        Sample size in bytes
        """
        return self.data.get("file_size")

    @lazy_property()
    def file_type(self):
        """
        Sample type
        """
        return self.data.get("file_type")

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

    def download(self):
        """
        Downloads file contents

        :return: File contents
        :rtype: str

        Example - download first file with size less than 1000 bytes and VBS extension

        .. code-block:: python

           dropper = next(mwdb.search_file('file.size:[0 TO 1000] AND file.name:"*.vbs"'))

           with open(dropper.file_name, "wb") as f:
               f.write(dropper.download())

           print("Downloaded {}".format(dropper.file_name))
        """
        token = self.api.post("request/sample/{id}".format(**self.data))["url"].split("/")[-1]
        return self.api.get("download/{}".format(token), raw=True)

    def download_content(self):
        """
        .. deprecated:: 2.3.0
           Use :py:meth:`download` instead.
        """
        warnings.warn("download_content() is deprecated. Use download() method.", DeprecationWarning)
        return self.download()
