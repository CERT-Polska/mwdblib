try:
    from .main import main

    from .comment import comment_command
    from .fetch import fetch_command
    from .get import get_command
    from .link import link_command
    from .list import list_command
    from .login import login_command, logout_command
    from .metakey import metakey_command
    from .search import search_command
    from .share import share_command
    from .tag import tag_command
    from .upload import upload_command

    __all__ = [
        "main",
        "comment_command",
        "fetch_command",
        "get_command",
        "link_command",
        "list_command",
        "login_command",
        "logout_command",
        "metakey_command",
        "search_command",
        "share_command",
        "tag_command",
        "upload_command"
    ]
except ImportError as e:
    import sys
    print("""
[!] It seems that you haven't installed extra dependencies needed by CLI extension.
    Best way to install them is to use `pip install mwdblib[cli]` command.
    If it doesn't help, let us know and create an issue: https://github.com/CERT-Polska/mwdblib/issues
    Missing dependency: {}""".format(e.name))
    sys.exit(1)
