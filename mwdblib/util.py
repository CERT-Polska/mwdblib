import hashlib
from typing import Any


def convert_to_utf8(obj: Any) -> bytes:
    """Encodes object into utf-8 bytes"""
    return bytes(str(obj), "utf-8")


def _eval_config_dhash(obj: Any) -> str:
    """Compute a data hash from the object. This is the hashing algorithm
    used internally by MWDB to assign unique ids to configs
    """
    if isinstance(obj, list):
        # For lists: evaluate hash recursively for all elements
        # and sort them lexicographically
        return _eval_config_dhash(str(sorted([_eval_config_dhash(o) for o in obj])))
    elif isinstance(obj, dict):
        # For dicts: convert to key-ordered tuples with hashed value
        return _eval_config_dhash(
            [[o, _eval_config_dhash(obj[o])] for o in sorted(obj.keys())]
        )
    else:
        # Other types: evaluate SHA256 after conversion to UTF-8
        return hashlib.sha256(convert_to_utf8(obj)).hexdigest()


def config_dhash(obj: Any) -> str:
    """
    Compute a data hash from the object. This is the hashing algorithm
    used internally by MWDB to assign unique ids to configs.

    .. versionchanged:: 3.3.0
        Added support for in-blob keys

    :param obj: Dict with configuration
    :type obj: dict
    :return: SHA256 hex digest
    """
    config = dict(obj)
    for key, value in config.items():
        if isinstance(value, dict) and list(value.keys()) == ["in-blob"]:
            in_blob = value["in-blob"]
            if isinstance(in_blob, dict):
                config[key]["in-blob"] = hashlib.sha256(
                    convert_to_utf8(in_blob["content"])
                ).hexdigest()
    return _eval_config_dhash(config)
