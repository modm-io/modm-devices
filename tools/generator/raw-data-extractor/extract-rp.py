from pathlib import Path
import urllib.request
import zipfile
import shutil
import io
import glob
import os

svdurls = [
    ["rp2040.svd","https://github.com/raspberrypi/pico-sdk/raw/master/src/rp2040/hardware_regs/rp2040.svd"]
]

shutil.rmtree("../raw-device-data/rp-devices", ignore_errors=True)
Path("../raw-device-data/rp-devices").mkdir(exist_ok=True, parents=True)

if __name__ == "__main__":
    dest = "../raw-device-data/rp-devices"
    for svdurl in svdurls:
        print("Downloading... " + svdurl[0])
        with urllib.request.urlopen(svdurl[1]) as content:
            file = Path(dest + '/' + svdurl[0])
            with file.open("w", encoding="utf-8") as wfile:
                wfile.writelines(content.read().decode("utf-8"))
        
