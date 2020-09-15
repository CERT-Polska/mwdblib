.. include:: <isonum.txt>

Data model
===============

MWDB organizes malware-related data using object model, which has been evolved from years of malware analysis and research in CERT.pl.
Objects are defined by set of attributes and relations including few loose conventions described below. The model is still being developed, so it could change a bit over time.

Object types
------------

In MWDB model, we can distinguish three types of objects:

- **Files** (sometimes called *samples*) are representing malware samples in various forms - executable files, memory dumps, archives etc.
- **Configs** containing structured malware data. These can be static configurations ripped from malware samples or parsed dynamic configurations from C&C servers, kept in JSON-like format.
- **Blobs** containing unstructured malware data, but usually in human-readable form. Blobs are raw configuration files, injects, strings, list of credentials, peers etc.
  Blobs are optimized for quick full-text searching. Blob can be also a part of config, being referred by one of its keys.

All objects are identified by SHA-256-based hash. For files and blobs it's just plain SHA-256.

Configs are hashed in order-insensitive way: keys and inner lists are sorted and then hashed using SHA-256 recursively.

Object relations
----------------

Next part of MWDB model are relations between objects. Each object can be associated with parent or child objects, which are somehow related with them.

Semantics of these relations are depending on object types:

File |rarr| File relations
^^^^^^^^^^^^^^^^^^^^^^^^^^

  These are the most common one. Child samples are usually next stage of infection chain, parts of its parent (embedded in file or contained in archive) or executable artifacts from parent execution.

  .. image:: _static/file-file-rel.png
     :width: 600

File |rarr| Config relations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  These type of relations are usually the most interesting, determining the association between sample and static configuration.
  Static configuration contains features and parameters determining malicious operations performed by sample:

  - Malware family
  - Hardcoded addresses of C&C servers
  - DGA seeds
  - Encryption keys used for communication
  - Malware version
  - Botnet/campaign ID
  - Module type etc.

  **It's not only about the IoCs**. Static configuration is the actual representation of unique malware. Various samples unpacking to the same configuration usually have the same, but differently packed core, which allows us to determine the similarity between these files. Format of configuration is depending on malware family, sometimes resulting from the structure "proposed" by malware author.

  .. image:: _static/file-config-rel.png
     :width: 400

Config |rarr| File relations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  These are the most misunderstood one. As said before, static configuration can be treated as group of samples representing actually the same malware. (Semi-)automated systems are trying to fetch additional drops and modules using data from specific static config object, so all dropped samples will be bound with config object.

  * Assume that bunch of obfuscated droppers/RATs from malspam have the same static configuration (distribution URLs). Dropped malware will be bound to this config instead of bounding to all of these samples.
  * Sometimes the actual operations of malware sample are depending on modules/plugins distributed by C&C. All fetched modules are stored in model as children of core static configuration.
  * Malicious servers are also distributing update for botnet clients, which are also depending on specific static configuration.

  .. image:: _static/config-file-rel.png
     :width: 600

Config |rarr| Blob relations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Not only the samples are distributed by C&C during campaign. Bankers are parametrized by dynamic configuration containing injects. Spam botnets are fetching spam templates. All of these text-like things can be stored as text blobs bound to related static configuration.

  Blobs can be also part of static configuration e.g. in form of raw configuration or multi-line values like ransom note. Important thing is to eliminate things that are originating from specific execution in sandbox and can't be considered as part of config e.g. random nonces, memory pointers and other noise.

  .. image:: _static/config-blob-rel.png
     :width: 400

Blob |rarr| Config relations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  In addition to "static" configuration type, we have also "dynamic" configurations, which are parsed form of text blob data fetched from C&C. Usually data distributed by malicious servers have some determined structure, which is parsed by malware sample, so we can extract the most important things and store them in more organized way.

Object tags
-----------

  Each object can be easily described using tags. There are few built-in conventions, which are exposed by coloring tags in similar way.

  * Ripped (extracted) sample
  .. image:: _static/tag-ripped.png
  * Known family
  .. image:: _static/tag-malware.png
  * Tags describing the source
  .. image:: _static/tag-feed.png
  * Tags describing the type of sample
  .. image:: _static/tag-dump.png
  .. image:: _static/tag-runnable.png
  * Tags inherited from the source
  .. image:: _static/tag-urlhaus.png

Object metakeys
---------------

  Metakeys (also called *Attributes*) are key-value pairs intended to store references to internal analytical systems.
  This part will most likely be redesigned soon, so it's dedicated for internal use only.
