# mwdblib

API bindings for [mwdb.cert.pl](https://mwdb.cert.pl) service or your own instance of [MWDB](https://github.com/CERT-Polska/mwdb-core).
Use it if you want to automate data uploading/fetching from MWDB or have some ipython-based CLI.

Latest version requires Python >= 3.7.

## Getting started

```console
$ pip install mwdblib

or with CLI

$ pip install mwdblib[cli]
$ mwdb version
```

The main interface is the MWDB object that provides various methods to interact with MWDB.

```python
>>> from mwdblib import MWDB
>>> mwdb = MWDB()
>>> mwdb.login()
Username: jkowalski
Password:

>>> files = mwdb.recent_files()
>>> file = next(files)
>>> file.name
'400000_1973838fc27536e6'
>>> file.tags
['dump:win32:exe', 'avemaria']
>>> file.children
[<mwdblib.file.MWDBConfig at ...>]
```

mwdblib provides also optional command line interface (CLI), which can be used to interact with a MWDB repository.
It requires `mwdblib[cli]` extras to be installed.

```console
$ mwdb --help

Usage: mwdb [OPTIONS] COMMAND [ARGS]...

  MWDB Core API client

Options:
  --help  Show this message and exit.

Commands:
  comment  Add comment to object
  fetch    Download object contents
  get      Get information about object
  link     Set relationship for objects
  list     List recent objects
  login    Store credentials for MWDB authentication
  logout   Reset stored credentials
  metakey  Add metakey to object
  search   Search objects using Lucene query
  server   Prints current server URL and version
  share    Share object with another group
  tag      Add/remove tags for objects
  upload   Upload object into MWDB
  version  Prints mwdblib version

$ mwdb login
Username: jkowalski
Password:
```

If you log in via CLI, your credentials will be stored in configuration file (`~/.mwdb`) and keyring. These are used by
default by `MWDB()` objects, so you don't have to login each time when you use e.g. IPython session to interact
with MWDB Core API.

## Using mwdblib with own MWDB Core instance

Default API endpoint that is used by mwdblib is `https://mwdb.cert.pl/api/` service (CERT.pl MWDB instance), but
mwdblib is able to work with self-hosted instances as well.

You can pass alternative MWDB endpoint via `api_url` parameter

```python
>>> mwdb = MWDB(api_url="https://<my-instance>/api/")
```

Alternative API endpoint is also supported by CLI component

```console
$ mwdb login --api-url https://<my-instance>/api/
Username: user
Password:

$ cat ~/.mwdb
[mwdb]
api_url = https://<my-instance>/api/

[mwdb:https://mwdb.cert.pl/api/]
username = jkowalski

[mwdb:http://<my-instance>/api/]
username = user
```

Used API endpoint will be remembered in configuration, so subsequent calls will apply to your own instance.
That configuration applies to the `MWDB()` objects as well.

## More information

Complete mwdblib API docs can be found here: https://mwdblib.readthedocs.io/en/latest/

Additional guidelines regarding MWDB REST API and automation can be found in MWDB Core documentation: https://mwdb.readthedocs.io/en/latest/user-guide/8-REST-and-mwdblib.html
