from pathlib import Path
import urllib.request
import zipfile
import shutil
import io
import glob
import os
import re

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

dl_page = "https://www.nordicsemi.com/Products/Development-tools/nRF-MDK/Download"
dest = "../raw-device-data/nrf-devices/nrf"

shutil.rmtree("../raw-device-data/nrf-devices", ignore_errors=True)
Path(dest).mkdir(exist_ok=True, parents=True)

with urllib.request.urlopen(urllib.request.Request(dl_page, headers=hdr)) as response:
    html = response.read().decode("utf-8")
    packurl = re.search('<span.*?>(.*?nsscprodmedia.*?/nrf_mdk_.*?_gcc_bsdlicense.zip)<', html)
    packurl = packurl.group(1)

print("Downloading...", packurl)
with urllib.request.urlopen(urllib.request.Request(packurl, headers=hdr)) as content:
    z = zipfile.ZipFile(io.BytesIO(content.read()))
    print("Extracting...")
    # remove subfolders, some packs have several chips per pack
    for zi in z.infolist():
        if zi.filename.endswith(".svd") or zi.filename.endswith(".ld"):
            zi.filename = os.path.basename(zi.filename)
            print(zi.filename)
            z.extract(zi, dest)

# dirty hack because af inconsistent part names in .svd files
os.rename(dest + '/nrf51.svd', dest + '/nrf51822.svd')
os.rename(dest + '/nrf52.svd', dest + '/nrf52832.svd')

for f in glob.glob(dest + '/nrf51_*.ld'):
    os.remove(f)
for f in glob.glob(dest + '/nrf52_*.ld'):
    os.remove(f)
for f in glob.glob(dest + '/nrf_common.ld'):
    os.remove(f)
