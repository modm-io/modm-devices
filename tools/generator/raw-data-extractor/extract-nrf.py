from pathlib import Path
import urllib.request
import zipfile
import shutil
import io
import os

packurl = "https://www.nordicsemi.com/-/media/Software-and-other-downloads/Desktop-software/nRF-MDK/sw/8-33-0/nRF_MDK_8_33_0_GCC_BSDLicense.zip"

shutil.rmtree("../raw-device-data/nrf-devices", ignore_errors=True)
Path("../raw-device-data/nrf-devices/nrf").mkdir(exist_ok=True, parents=True)

if __name__ == "__main__":
    dest = "../raw-device-data/nrf-devices/nrf"
    print("Downloading...")
    with urllib.request.urlopen(packurl) as content:
        z = zipfile.ZipFile(io.BytesIO(content.read()))
        print("Extracting...")
        # remove subfolders, some packs have several chips per pack
        for zi in z.infolist():
            if zi.filename.endswith(".svd"):
                zi.filename = os.path.basename(zi.filename)
                print(zi.filename)
                z.extract(zi, dest)

    # dirty hack because af inconsistent part names in .svd files
    os.rename(dest + '/nrf51.svd', dest + '/nrf51822.svd')
    os.rename(dest + '/nrf52.svd', dest + '/nrf52832.svd')
