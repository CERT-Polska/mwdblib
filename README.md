# mwdblib

mwdb.cert.pl API bindings for Python 2.x/3.x. Use it if you want to automate data uploading/fetching from mwdb.cert.pl or have some ipython-based CLI :)

## Usage

Print names and tags of 25 recent files

```python
from mwdblib import Malwarecage
from itertools import islice

mwdb = Malwarecage()
mwdb.login("admin", "password123")

# recent_files is generator, do not execute list(recent_files) without islice!
files = list(islice(mwdb.recent_files(), 25))
print [(f.file_name, f.tags) for f in files]
```

Find all Netwire configs
```python
configs = mwdb.search("static.family:netwire")

print [c.cfg for c in configs]
```

Download file with hash
```python
h = "3629344675705286607dd0f680c66c19f7e310a1"
file = mwdb.query_file(h)

with open(h, "wb") as f:
    f.write(file.download_content())
```

Download first file with size less than 1000 bytes and VBS extension
```python
dropper = mwdb.search('file.size:[0 TO 1000] AND file.name:"*.vbs"')[0]

with open(dropper.file_name, "wb") as f:
    f.write(dropper.download_content())
    
print "Downloaded {}".format(dropper.file_name)
```

Get list of all files dropped by `3629344675705286607dd0f680c66c19f7e310a1`
```python
from mwdblib.file import MalwarecageFile

file = mwdb.query_file("3629344675705286607dd0f680c66c19f7e310a1")
print [(child.file_name, child.sha256, child.tags) for child in file.children if isinstance(child, MalwarecageFile)]
```

Print all comments which contains "malware"
```python
files = mwdb.search('file.comment:"*malware*"')
for f in files:
    for cm in f.comments:
        if "malware" in cm.comment:
            print "{}: {}".format(f.id, cm.comment)
```

Get upload time of last sample commented "malware"
```python
print mwdb.search('file.comment:"*malware*"').next().upload_time
```

Get metakey cuckoo_id for file `e46e4aadc462cd9b70e44610afd6b549` (if used with Malwarecage)

```python
file = mwdb.query_file("e46e4aadc462cd9b70e44610afd6b549")
print "Cuckoo IDs is {}".format(file.metakeys.get("cuckoo_id"))
```

Use local Malwarecage 2 instance with pregenerated token
```python
from mwdblib.api import MalwarecageAPI
from mwdblib import Malwarecage

api = MalwarecageAPI("http://localhost:8080", "tokentokentoken")
mwdb = Malwarecage(api)
```

Use local Malwarecage 2 instance in testing enviroment
```python
import mwdblib

api = mwdblib.MalwarecageAPI("http://localhost:5000")
m = mwdblib.Malwarecage(api)
m.login("admin", "admin")
```
