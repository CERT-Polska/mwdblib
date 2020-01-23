Getting data automatically from Malwarecage
===========================================

Looking for recently uploaded files and retrieving them if file type contains "PE32":

.. code-block:: python

    from mwdblib import Malwarecage

    mwdb = Malwarecage(api_key="<secret>")

    def report_new_sample(sample):
        print("Found new sample {} ({})".format(sample.name, sample.sha256))
        if "PE32" in sample.type:
            with open(sample.id, "wb") as f:
                f.write(sample.download())
            print("[+] PE32 downloaded successfully!")

    for sample in mwdb.listen_for_files():
        report_new_sample(sample)

Sometimes you want to keep track of the latest reported sample between script executions.
Mwdblib doesn't concern itself with persistence - you need to store the latest reported object ID on your own.

.. code-block:: python

    from mwdblib import Malwarecage

    mwdb = Malwarecage(api_key="<secret>")


    def store_last(last_id):
        with open("last_id", "w") as f:
            f.write(last_id)

    def load_last():
        try:
            with open("last_id", "r") as f:
                return f.read()
        except IOError:
            return None

    def report_new_sample(sample):
        print("Found new sample {} ({})".format(sample.name, sample.sha256))
        if "PE32" in sample.type:
            with open(sample.id, "wb") as f:
                f.write(sample.download())
            print("[+] PE32 downloaded successfully!")


    last_id = load_last()
    for sample in mwdb.listen_for_files(last_id):
        report_new_sample(sample)
        store_last(sample.id)

