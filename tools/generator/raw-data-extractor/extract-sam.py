
import urllib.request
import zipfile
import re, io, os
import shutil

from pathlib import Path
from multiprocessing import Pool
from collections import defaultdict
from distutils.version import StrictVersion


packurl = "http://packs.download.atmel.com/"

shutil.rmtree("../raw-device-data/sam-devices", ignore_errors=True)
Path("../raw-device-data/sam-devices").mkdir(exist_ok=True, parents=True)

with urllib.request.urlopen(packurl) as response:
    html = response.read().decode("utf-8")
    family_links = defaultdict(list)
    for link, family, version in re.findall(r'data-link="(Atmel\.(SAM.*?)_DFP\.(.*?)\.atpack)"', html):
        family_links[family].append((link, StrictVersion(version),))
    # Choose only the latest version of the atpack
    family_links = [(family, sorted(data, key=lambda d: d[1])[-1][0])
                    for family, data in family_links.items()]

def dl(family_link):
    family, link, = family_link
    dest = "../raw-device-data/sam-devices/{}".format(family.lower())
    print("Downloading '{}'...".format(link))

    with urllib.request.urlopen(packurl + link) as content:
        z = zipfile.ZipFile(io.BytesIO(content.read()))
        print("Extracting '{}'...".format(link))
        # remove subfolders, some packs have several chips per pack
        for zi in z.infolist():
            if zi.filename.endswith(".atdf"):
                zi.filename = os.path.basename(zi.filename)
                z.extract(zi, dest)

if __name__ == "__main__":
    with Pool(len(family_links)) as p:
        p.map(dl, family_links)

# shutil.copy("patches/sam.patch", "../raw-device-data")
# os.system("(cd ../raw-device-data; patch -p1 -f --input=sam.patch)")
# os.remove("../raw-device-data/sam.patch")
