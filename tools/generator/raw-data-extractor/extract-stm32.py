
from pathlib import Path
import urllib.request
import zipfile
import shutil
import re
import io
import os

data_path = "../raw-device-data/stm32-devices/"
# First check STMUpdaterDefinitions.xml from this zip
update_url = "http://sw-center.st.com/packs/resource/utility/updaters.zip"
# Then Release="MX.6.2.0" maps to this: -win, -lin, -mac
cube_url = "http://sw-center.st.com/packs/resource/library/stm32cube_mx_v{}-lin.zip"

# Set the right headers
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

print("Downloading Update Info...")
print(update_url)
with urllib.request.urlopen(urllib.request.Request(update_url, headers=hdr)) as content:
    z = zipfile.ZipFile(io.BytesIO(content.read()))
    with io.TextIOWrapper(z.open("STMUpdaterDefinitions.xml"), encoding="utf-8") as defs:
        version = re.search(r'Release="MX\.(.*?)"', defs.read())
        version = version.group(1).replace(".", "")

shutil.rmtree(data_path, ignore_errors=True)
Path(data_path).mkdir(exist_ok=True, parents=True)

print("Downloading Database...")
print(cube_url.format(version))
with urllib.request.urlopen(urllib.request.Request(cube_url.format(version), headers=hdr)) as content:
    z = zipfile.ZipFile(io.BytesIO(content.read()))
    print("Extracting Database...")
    for file in z.namelist():
        if any(file.startswith(prefix) for prefix in ("MX/db/mcu", "MX/db/plugins")):
            z.extract(file, data_path)

print("Moving Database...")
shutil.move(data_path+"MX/db/mcu", data_path+"mcu")
shutil.move(data_path+"MX/db/plugins", data_path+"plugins")
shutil.rmtree(data_path+"MX", ignore_errors=True)

print("Patching Database...")
shutil.copy("patches/stm32.patch", "../raw-device-data")
os.system("(cd ../raw-device-data; patch -p1 -l -i stm32.patch)")
os.remove("../raw-device-data/stm32.patch")

