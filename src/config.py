from .object import MalwarecageObject, lazy_property


class MalwarecageConfig(MalwarecageObject):
    URL_PATTERN = "config/{id}"

    @staticmethod
    def create(api, data):
        return MalwarecageConfig(api, data)

    def _update(self, data):
        if "cfg" in data:
            from .blob import MalwarecageBlob
            data = dict(data)
            data["config"] = {k: (MalwarecageBlob(self.api, {"id": v["in-blob"]})
                                  if isinstance(v, dict) and "in-blob" in v
                                  else v)
                              for k, v in data["cfg"].items()}
        super(MalwarecageConfig, self)._update(data)

    @lazy_property()
    def family(self):
        """
        Configuration family
        """
        return self.data.get("family")

    @lazy_property()
    def type(self):
        """
        Configuration type ('static' or 'dynamic')
        """
        return self.data.get("config_type")

    @lazy_property()
    def cfg(self):
        """
        dict object with configuration
        """
        return self.data.get("config")

    @lazy_property()
    def config_dict(self):
        """
        raw dict object with configuration
        (in-blob keys are not mapped to :class:`MalwarecageBlob` objects)
        """
        return self.data.get("cfg")

    @property
    def config(self):
        """
        dict object with configuration

        .. seealso:: :py:attr:`config_dict`
        """
        return self.cfg
