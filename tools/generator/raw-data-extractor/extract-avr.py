
from pathlib import Path
from multiprocessing import Pool
import urllib.request
import zipfile
import shutil
import re
import io
import os

families = [
    "ATtiny", "ATmega",
    "XMEGAA", "XMEGAB", "XMEGAC", "XMEGAD", "XMEGAE"
]
packurl = "http://packs.download.microchip.com/"

shutil.rmtree("../raw-device-data/avr-devices", ignore_errors=True)
Path("../raw-device-data/avr-devices").mkdir(exist_ok=True, parents=True)

with urllib.request.urlopen(packurl) as response:
    html = response.read().decode("utf-8")
def dl(family):
    atpack = re.search(r'data-link="(Microchip\.{}_DFP\..*?\.atpack)"'.format(family), html).group(1)
    dest = "../raw-device-data/avr-devices/{}".format(family.lower())
    print("Downloading '{}'...".format(atpack))
    with urllib.request.urlopen(packurl + atpack) as content:
        z = zipfile.ZipFile(io.BytesIO(content.read()))
        print("Extracting '{}'...".format(atpack))
        for member in [m for m in z.namelist() if m.startswith("atdf/")]:
            z.extract(member, dest+"_")
    shutil.move(dest+"_/atdf", dest)
    shutil.rmtree(dest+"_", ignore_errors=True)

if __name__ == "__main__":
    with Pool(len(families)) as p:
        p.map(dl, families)

    shutil.copy("patches/avr.patch", "../raw-device-data")
    os.system("(cd ../raw-device-data; patch -p1 -l --no-backup-if-mismatch -i avr.patch)")
    os.remove("../raw-device-data/avr.patch")
