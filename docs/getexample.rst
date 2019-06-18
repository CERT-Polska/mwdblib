Getting data automatically from Malwarecage
===========================================

Looking for recently uploaded files and retrieving them if file type contains "PE32":

.. code-block:: python

    import itertools
    import time

    from mwdblib import Malwarecage

    mwdb = Malwarecage(api_key="<secret>")

    def report_new_sample(sample):
        print("Found new sample {} ({})".format(sample.name, sample.sha256))
        if "PE32" in sample.type:
            with open(sample.id, "wb") as f:
                f.write(sample.download())
            print("[+] PE32 downloaded successfully!")

    last_sample = None
    while True:
         top_sample = next(mwdb.recent_samples()).id

         if last_sample is not None:
             for sample in itertools.takewhile(lambda s: s.id != last_sample.id,
                                               mwdb.recent_samples()):
                 report_new_sample(sample)

         last_sample = top_sample
         # Wait 10 minutes before next try
         time.sleep(600)
