
from pathlib import Path
from multiprocessing import Pool
import urllib.request
import zipfile
import shutil
import re
import io
import os

families = [
    "SAMD21", "SAMD51",
]
packurl = "http://packs.download.atmel.com/"

shutil.rmtree("../raw-device-data/sam-devices", ignore_errors=True)
Path("../raw-device-data/sam-devices").mkdir(exist_ok=True, parents=True)

with urllib.request.urlopen(packurl) as response:
    html = response.read().decode("utf-8")
def dl(family):
    atpack = re.search(r'data-link="(Atmel\.{}_DFP\..*?\.atpack)"'.format(family), html).group(1)
    dest = "../raw-device-data/sam-devices/{}".format(family.lower())
    print("Downloading '{}'...".format(atpack))
    with urllib.request.urlopen(packurl + atpack) as content:
        z = zipfile.ZipFile(io.BytesIO(content.read()))
        print("Extracting '{}'...".format(atpack))
        # remove subfolders, some packs have several chips per pack
        for zi in z.infolist():
            if zi.filename.endswith(".atdf"):
                zi.filename = os.path.basename(zi.filename)
                z.extract(zi, dest)

if __name__ == "__main__":
    with Pool(len(families)) as p:
        p.map(dl, families)

# shutil.copy("patches/sam.patch", "../raw-device-data")
# os.system("(cd ../raw-device-data; patch -p1 -f --input=sam.patch)")
# os.remove("../raw-device-data/sam.patch")
