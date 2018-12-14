from .obj import MalwarecageObject, lazy_property


class MalwarecageFile(MalwarecageObject):
    URL_PATTERN = "file/{id}"

    @lazy_property()
    def md5(self):
        return self.data.get("md5")

    @lazy_property()
    def sha1(self):
        return self.data.get("sha1")

    @lazy_property()
    def sha256(self):
        return self.data.get("sha256")

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
        return self.data.get("file_name")

    @lazy_property()
    def file_size(self):
        return self.data.get("file_size")

    @lazy_property()
    def file_type(self):
        return self.data.get("file_type")

    def download_content(self):
        token = self.api.post("request/sample/{id}".format(**self.data))["url"].split("/")[-1]
        return self.api.get("download/{}".format(token), raw=True)
