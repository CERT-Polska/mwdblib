import hashlib
import sys


def convert_to_utf8(obj):
    """Encodes object into utf-8 bytes (or 'str' in Py2)"""
    obj = str(obj)
    if sys.version_info[0] == 3:
        obj = bytes(obj, "utf-8")
    else:
        obj = u''.join(map(unichr, map(ord, obj))).encode("utf-8")  # noqa: F821 in Py3 context
    return obj


def config_dhash(obj):
    """ Compute a data hash from the object. This is the hashing algorithm
    used internally by malwarecage to assign unique ids to configs
    """
    if isinstance(obj, list):
        # For lists: evaluate hash recursively for all elements and sort them lexicographically
        return config_dhash(str(sorted([config_dhash(o) for o in obj])))
    elif isinstance(obj, dict):
        # For dicts: convert to key-ordered tuples with hashed value
        return config_dhash(
            [[o, config_dhash(obj[o])] for o in sorted(obj.keys())]
        )
    else:
        # Other types: evaluate SHA256 after conversion to UTF-8
        return hashlib.sha256(convert_to_utf8(obj)).hexdigest()
