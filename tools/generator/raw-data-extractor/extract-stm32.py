
from pathlib import Path
from multiprocessing import Pool
import urllib.request
import zipfile
import shutil
import re
import io
import os

cubeurl = "https://www.st.com/content/st_com/en/products/development-tools/"\
		  "software-development-tools/stm32-software-development-tools/"\
		  "stm32-configurators-and-code-generators/stm32cubemx.html"

# Set the right headers
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

with urllib.request.urlopen(urllib.request.Request(cubeurl, headers=hdr)) as response:
    html = response.read().decode("utf-8")
    dlurl = re.search(r'data-download-path="(/content/ccc/resource/.*?\.zip)"', html).group(1)
    dlurl = "https://www.st.com" + dlurl
    print("Downloading CubeMX...")
    print(dlurl)

shutil.rmtree("temp-stm32", ignore_errors=True)
with urllib.request.urlopen(urllib.request.Request(dlurl, headers=hdr)) as content:
    z = zipfile.ZipFile(io.BytesIO(content.read()))
    item = [n for n in z.namelist() if ".exe" in n][0]
    print("Extracting SetupSTM32CubeMX.exe...")
    z = zipfile.ZipFile(io.BytesIO(z.read(item)))
    print("Extracting Core-Pack...")
    z.extract("resources/packs/pack-Core", "temp-stm32/")

print("Compiling IzPackDeserializer...")
Path("temp-stm32/bin/izpack_deserializer").mkdir(exist_ok=True, parents=True)
Path("temp-stm32/bin/com/izforge/izpack/api/data").mkdir(exist_ok=True, parents=True)
os.system("javac izpack/*.java")
shutil.move("izpack/IzPackDeserializer.class", "temp-stm32/bin/izpack_deserializer/")
for f in Path("izpack/").glob("*.class"):
	shutil.move(str(f), "temp-stm32/bin/com/izforge/izpack/api/data/")

print("Extracting Database...")
os.system("(cd temp-stm32/bin; java izpack_deserializer.IzPackDeserializer > /dev/null)")

print("Moving Database...")
shutil.rmtree("../raw-device-data/stm32-devices", ignore_errors=True)
Path("../raw-device-data/stm32-devices").mkdir(exist_ok=True, parents=True)
shutil.move("temp-stm32/output/db/mcu", "../raw-device-data/stm32-devices/")
shutil.move("temp-stm32/output/db/plugins", "../raw-device-data/stm32-devices/")

print("Patching Database...")
shutil.copy("patches/stm32.patch", "../raw-device-data")
os.system("(cd ../raw-device-data; patch -p1 -l -i stm32.patch)")
os.remove("../raw-device-data/stm32.patch")
