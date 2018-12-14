from .obj import MalwarecageObject, lazy_property


class MalwarecageConfig(MalwarecageObject):
    URL_PATTERN = "config/{id}"

    @lazy_property()
    def family(self):
        return self.data.get("family")

    @lazy_property()
    def cfg(self):
        return self.data.get("cfg")
