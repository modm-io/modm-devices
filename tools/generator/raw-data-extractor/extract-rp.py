from pathlib import Path
import urllib.request
import shutil
import os

svdurls = [
    ["rp2040.svd","https://github.com/raspberrypi/pico-sdk/raw/master/src/rp2040/hardware_regs/RP2040.svd"],
    ["rp2350.svd","https://github.com/raspberrypi/pico-sdk/raw/master/src/rp2350/hardware_regs/RP2350.svd"]
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


# print("Patching Database...", flush=True)
# shutil.copy("patches/rp2040.patch", "../raw-device-data")
# os.system("(cd ../raw-device-data; patch -p1 -l -i rp2040.patch)")
# os.remove("../raw-device-data/rp2040.patch")
