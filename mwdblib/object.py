import datetime
import warnings
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union, cast

from .api import APIClient

if TYPE_CHECKING:
    from .comment import MWDBComment
    from .karton import MWDBKartonAnalysis
    from .share import MWDBShare

MWDBElementData = Dict[str, Any]
MWDBElementDataMapper = Callable[[MWDBElementData], Any]


class MWDBElement:
    """
    Represents any MWDB entity that can be loaded from API
    """

    def __init__(self, api: APIClient, data: MWDBElementData) -> None:
        self.api = api
        self.data = dict(data)

    def _load(
        self, url_pattern: str, mapper: Optional[MWDBElementDataMapper] = None
    ) -> None:
        """
        Attribute lazy-loading method.
        """
        data = self.api.get(url_pattern.format(**self.data))
        if mapper is not None:
            data = mapper(data)
        self.data.update(data)

    def _expire(self, key: str) -> None:
        """
        Cached attribute value expiration
        """
        if key in self.data:
            del self.data[key]


class MWDBObject(MWDBElement):
    """
    Represents abstract, generic MWDB object.

    Should never be instantiated directly.

    If you really need to get synthetic instance - use internal
    :py:meth:`create` static method.
    """

    URL_TYPE: str = "object"  # Type name in URL endpoint
    TYPE: str = "object"  # Type name in 'type' object field

    def _load(
        self,
        url_pattern: Optional[str] = None,
        mapper: Optional[MWDBElementDataMapper] = None,
    ) -> None:
        if url_pattern is None:
            url_pattern = self.URL_TYPE + "/{id}"
        return super()._load(url_pattern, mapper=mapper)

    @staticmethod
    def create(api: APIClient, data: MWDBElementData) -> "MWDBObject":
        """
        Creates specialized MWDBObject subclass instance based on specified ``data``
        """
        from .blob import MWDBBlob
        from .config import MWDBConfig
        from .file import MWDBFile

        type = data["type"]
        if type == MWDBFile.TYPE:
            return MWDBFile(api, data)
        elif type == MWDBConfig.TYPE:
            return MWDBConfig(api, data)
        elif type == MWDBBlob.TYPE:
            return MWDBBlob(api, data)
        raise RuntimeError(f"Unsupported object type: '{type}'")

    def remove(self) -> None:
        """
        Remove specific object from mwdb

        The object should be treated as invalidated after using this method .
        """
        self.api.delete("object/{}".format(self.data["id"]))
        self.flush()

    @property
    def id(self) -> str:
        """
        Object identifier (sha256)
        """
        return cast(str, self.data["id"])

    @property
    def object_type(self) -> str:
        """
        Object type ('file', 'static_config' or 'text_blob')
        """
        return cast(str, self.data["type"])

    @property
    def sha256(self) -> str:
        """
        Object identifier (sha256)
        """
        return self.id

    @property
    def tags(self) -> List[str]:
        """
        Returns list of tags

        :return: List of tags
        """
        if "tags" not in self.data:
            self._load("object/{id}/tag", mapper=lambda data: {"tags": data})
        return [t["tag"] for t in self.data["tags"]]

    @property
    def comments(self) -> List["MWDBComment"]:
        """
        Returns list of comments

        :return: List of comment objects

        Example - print all comments of last object commented as "malware":

        .. code-block:: python

            comments = next(mwdb.search_files('comment:"*malware*"')).comments
            for comment in comments:
                print("{} {}".format(comment.author, comment.comment))
        """
        from .comment import MWDBComment

        if "comments" not in self.data:
            self._load("object/{id}/comment", mapper=lambda data: {"comments": data})
        return [
            MWDBComment(self.api, comment, self) for comment in self.data["comments"]
        ]

    @property
    def shares(self) -> List["MWDBShare"]:
        """
        Returns list of shares

        :return: List of share objects
        """
        from .share import MWDBShare

        if "shares" not in self.data:
            self._load(
                "object/{id}/share",
                mapper=lambda data: {"shares": data.get("shares", [])},
            )
        return [MWDBShare(self.api, share, self) for share in self.data["shares"]]

    @APIClient.requires("2.6.0")
    def _get_attributes(self) -> Dict[str, List[Any]]:
        if "attributes" not in self.data:
            self._load("object/{id}/attribute")
        result = defaultdict(list)
        for m in self.data["attributes"]:
            result[m["key"]].append(m["value"])
        return dict(result)

    @_get_attributes.fallback("2.0.0")
    def _get_attributes_fallback(self) -> Dict[str, List[Any]]:
        # Fallback to older metakey API
        return self._get_metakeys()

    @property
    def attributes(self) -> Dict[str, List[Any]]:
        """
        Returns dict object with attributes.

        Supports JSON-like values in MWDB Core >= 2.6.0.

        .. versionadded:: 4.0.0

        :return: Dict object containing attributes
        """
        return cast(Dict[str, List[Any]], self._get_attributes())

    def _get_metakeys(self) -> Dict[str, List[str]]:
        if "metakeys" not in self.data:
            self._load("object/{id}/meta")
        result = defaultdict(list)
        for m in self.data["metakeys"]:
            result[m["key"]].append(m["value"])
        return dict(result)

    @property
    def metakeys(self) -> Dict[str, List[str]]:
        """
        Returns dict object with metakeys.

        JSON-like values are coerced to strings for backwards compatibility.

        .. deprecated:: 4.0.0
           Use :py:attr:`attributes` instead

        :return: Dict object containing metakey attributes
        """
        warnings.warn(
            "'metakeys' attribute is deprecated. Use 'attributes' instead.",
            DeprecationWarning,
        )
        return self._get_metakeys()

    @property
    def upload_time(self) -> "datetime.datetime":
        """
        Returns timestamp of first object upload

        :return: datetime object with object upload timestamp
        """
        if "upload_time" not in self.data:
            self._load()
        return datetime.datetime.fromisoformat(self.data["upload_time"])

    @property
    def parents(self) -> List["MWDBObject"]:
        """
        Returns list of parent objects

        :return: List of parent objects
        """
        if "parents" not in self.data:
            self._load()
        return [self.create(self.api, parent) for parent in self.data["parents"]]

    @property
    def children(self) -> List["MWDBObject"]:
        """
        Returns list of child objects

        :return: List of child objects
        """
        if "children" not in self.data:
            self._load()
        return [self.create(self.api, child) for child in self.data["children"]]

    @property  # type: ignore
    @APIClient.requires("2.3.0")
    def analyses(self) -> List["MWDBKartonAnalysis"]:
        """
        Returns list of Karton analyses related with this object

        Requires MWDB Core >= 2.3.0.

        .. versionadded:: 4.0.0
        """
        from .karton import MWDBKartonAnalysis

        if "analyses" not in self.data:
            self._load(
                "object/{id}/karton",
                mapper=lambda data: {"analyses": data.get("analyses", [])},
            )
        return [
            MWDBKartonAnalysis(self.api, analysis) for analysis in self.data["analyses"]
        ]

    @property
    def content(self) -> bytes:
        """
        Returns stringified contents of object

        .. versionadded:: 3.0.0
           Added :py:attr:`MWDBObject.content` property
        """
        raise NotImplementedError()

    def add_child(self, child: Union["MWDBObject", str]) -> None:
        """
        Adds reference to child with current object as parent

        :param child: Object or object identifier (sha256)
        :type child: MWDBObject or str
        """
        if not isinstance(child, str):
            child = child.id
        self.api.put(
            "object/{parent}/child/{child}".format(parent=self.id, child=child)
        )
        self._expire("children")

    def add_tag(self, tag: str) -> None:
        """
        Tags object using specified tag

        :param tag: Tag string
        :type tag: str
        """
        self.api.put("object/{id}/tag".format(**self.data), json={"tag": tag})
        self._expire("tags")

    def remove_tag(self, tag: str) -> None:
        """
        Untags object using specified tag

        :param tag: Tag string
        :type tag: str
        """
        self.api.delete("object/{id}/tag".format(**self.data), params={"tag": tag})
        self._expire("tags")

    def add_comment(self, comment: str) -> None:
        """
        Adds comment

        :param comment: Comment string
        :type comment: str
        """
        self.api.post(
            "object/{id}/comment".format(**self.data), json={"comment": comment}
        )
        self._expire("comments")

    @APIClient.requires("2.6.0")
    def add_attribute(self, key: str, value: Any) -> None:
        """
        Adds attribute.

        Key can't be 'karton'. If you want to assign an analysis,
        use :py:meth:`assign_analysis` instead or use :py:meth:`add_metakey` method.

        .. versionadded:: 4.0.0

        :param key: Attribute key
        :type key: str
        :param value: Attribute value
        :type value: Any (JSON-like object)
        """
        if key == "karton":
            # This will fallback to add_metakey
            raise ValueError(
                "'karton' attribute key is no longer supported."
                "Use 'assign_analysis' method instead."
            )
        self.api.post(
            "object/{id}/attribute".format(**self.data),
            json={"key": key, "value": value},
        )
        self._expire("attributes")
        self._expire("metakeys")

    @add_attribute.fallback("2.0.0")
    def add_attribute_fallback(self, key: str, value: str) -> None:
        self._add_metakey(key, value)

    def _add_metakey(self, key: str, value: str) -> None:
        if type(value) is not str:
            raise TypeError(
                "Value types other than 'str' are not supported by this API. "
                "Check version of MWDB Core server or use add_attribute instead "
                "of add_metakey."
            )
        self.api.post(
            "object/{id}/meta".format(**self.data), json={"key": key, "value": value}
        )
        self._expire("attributes")
        self._expire("metakeys")

    def add_metakey(self, key: str, value: str) -> None:
        """
        Adds metakey attribute (string only)

        .. deprecated:: 4.0.0
           Use :py:attr:`add_attribute` instead

        :param key: Attribute key
        :type key: str
        :param value: Attribute value
        :type value: str
        """
        warnings.warn(
            "'add_metakey' method is deprecated, use 'add_attribute' instead",
            DeprecationWarning,
        )
        if key == "karton":
            warnings.warn(
                "'karton' attribute key is deprecated for assigning an analysis. "
                "Use 'assign_analysis' method instead.",
                DeprecationWarning,
            )
        self._add_metakey(key, value)

    @APIClient.requires("2.3.0")
    def reanalyze(
        self, arguments: Optional[Dict[str, Any]] = None
    ) -> "MWDBKartonAnalysis":
        """
        Submits new Karton analysis for given object.

        Requires MWDB Core >= 2.3.0.

        :param arguments: |
            Optional, additional arguments for analysis.
            Reserved for future functionality.

        .. versionadded:: 4.0.0
        """
        from .karton import MWDBKartonAnalysis

        arguments = {"arguments": arguments or {}}
        analysis = self.api.post(
            "object/{id}/karton".format(**self.data), json=arguments
        )
        self._expire("analyses")
        return MWDBKartonAnalysis(self.api, analysis)

    @APIClient.requires("2.3.0")
    def assign_analysis(self, analysis_id: str) -> "MWDBKartonAnalysis":
        """
        Assigns object to existing Karton analysis

        Requires MWDB Core >= 2.3.0.

        :param analysis_id: Karton analysis UUID

        .. versionadded:: 4.0.0
        """
        from .karton import MWDBKartonAnalysis

        analysis = self.api.put(f"object/{self.id}/karton/{analysis_id}")
        self._expire("analyses")
        return MWDBKartonAnalysis(self.api, analysis)

    def share_with(self, group: str) -> None:
        """
        Share object with specified group

        .. versionadded:: 3.0.0
           Added :py:meth:`MWDBObject.share_with` method

        :param group: Group name
        :type group: str
        """
        self.api.put("object/{id}/share".format(**self.data), json={"group": group})
        self._expire("shares")

    def flush(self) -> None:
        """
        Flushes local object state in case of pending updates.
        All object-specific properties will be lazy-loaded using API
        """
        self.data = {"id": self.data["id"], "type": self.data["type"]}
