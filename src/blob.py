from .obj import MalwarecageObject, lazy_property


class MalwarecageBlob(MalwarecageObject):
    URL_PATTERN = "blob/{id}"

    @lazy_property()
    def blob_name(self):
        return self.data.get("blob_name")

    @lazy_property()
    def blob_size(self):
        return self.data.get("blob_size")

    @lazy_property()
    def blob_type(self):
        return self.data.get("blob_type")

    @lazy_property()
    def content(self):
        return self.data.get("content")

    @lazy_property()
    def last_seen(self):
        import dateutil.parser
        return dateutil.parser.parse(self.data["last_seen"]) if "last_seen" in self.data else None
