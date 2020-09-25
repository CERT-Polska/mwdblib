from .object import MWDBObject


class MWDBConfig(MWDBObject):
    URL_TYPE = "config"
    TYPE = "static_config"

    @property
    def family(self):
        """
        Configuration family
        """
        if "family" not in self.data:
            self._load()
        return self.data["family"]

    @property
    def type(self):
        """
        Configuration type ('static' or 'dynamic')
        """
        if "config_type" not in self.data:
            self._load()
        return self.data["config_type"]

    @property
    def config_dict(self):
        """
        raw dict object with configuration
        (in-blob keys are not mapped to :class:`MWDBBlob` objects)
        """
        if "cfg" not in self.data:
            self._load()
        return self.data["cfg"]

    def _map_blobs(self, config):
        from .blob import MWDBBlob
        return {
            key: (
                MWDBBlob(self.api, {"id": value["in-blob"]})
                if isinstance(value, dict) and "in-blob" in value
                else value
            ) for key, value in config.items()
        }

    @property
    def config(self):
        """
        dict object with configuration
        """
        return self._map_blobs(self.config_dict)

    @property
    def content(self):
        """
        Returns raw dict object as JSON bytes

        :rtype: bytes
        """
        import json
        content = json.dumps(self.config_dict, indent=4)
        # Py2/Py3 compatibility
        if not isinstance(content, bytes):
            content = content.encode("utf-8")
        return content

    @property
    def cfg(self):
        """
        dict object with configuration

        .. seealso:: :py:attr:`config_dict`
        """
        return self.config


# Backwards compatibility
MalwarecageConfig = MWDBConfig
