import json
from typing import Any, Dict, cast

from .object import MWDBObject


class MWDBConfig(MWDBObject):
    URL_TYPE = "config"
    TYPE = "static_config"

    @property
    def family(self) -> str:
        """
        Configuration family
        """
        if "family" not in self.data:
            self._load()
        return cast(str, self.data["family"])

    @property
    def type(self) -> str:
        """
        Configuration type ('static' or 'dynamic')
        """
        if "config_type" not in self.data:
            self._load()
        return cast(str, self.data["config_type"])

    @property
    def config_dict(self) -> Dict[str, Any]:
        """
        Raw dict object with configuration
        (in-blob keys are not mapped to :class:`MWDBBlob` objects)
        """
        if "cfg" not in self.data:
            self._load()
        return cast(Dict[str, Any], self.data["cfg"])

    def _map_blobs(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps in-blob keys to MWDBBlob objects
        """
        from .blob import MWDBBlob

        return {
            key: (
                MWDBBlob(self.api, {"id": value["in-blob"]})
                if isinstance(value, dict) and "in-blob" in value
                else value
            )
            for key, value in config.items()
        }

    @property
    def config(self) -> Dict[str, Any]:
        """
        dict object with configuration. In-blob keys are mapped to MWDBBlob objects.
        """
        return self._map_blobs(self.config_dict)

    @property
    def content(self) -> bytes:
        """
        Returns raw dict object as JSON bytes

        :rtype: bytes
        """
        return json.dumps(self.config_dict, indent=4).encode()

    @property
    def cfg(self) -> Dict[str, Any]:
        """
        Raw dict object with configuration

        .. seealso:: :py:attr:`config_dict`
        """
        return self.config
