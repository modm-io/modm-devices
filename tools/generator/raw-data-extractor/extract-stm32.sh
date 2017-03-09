#!/usr/bin/env bash

# create temp dir
rm -r temp bin output
mkdir temp output

# download software
cubeurl="http://www.st.com/content/st_com/en/products/development-tools/software-development-tools/stm32-software-development-tools/stm32-configurators-and-code-generators/stm32cubemx.html"
dlurl=$(curl -s $cubeurl | ack "data-download-path=\"(?P<url>/content/ccc/resource/.*?\.zip)\"" --output "http://www.st.com\$+{url}")
echo $dlurl
curl -z stm32cubemx.zip -o stm32cubemx.zip $dlurl

# extract in two steps
echo "Expanding stm32cubemx.zip..."
unzip -q stm32cubemx.zip -d temp
unzip -a -q temp/SetupSTM32CubeMX-*.exe -d temp
chmod -R a+rxw temp

# compile izpack extractor
javac izpack/*.java
mkdir -p bin/izpack_deserializer
mv izpack/IzPackDeserializer.class bin/izpack_deserializer/
mkdir -p bin/com/izforge/izpack/api/data
mv izpack/*.class bin/com/izforge/izpack/api/data/

# run izpack extractor
echo "Extracting database..."
cd bin
java izpack_deserializer.IzPackDeserializer > /dev/null
cd ..

# move the juicy bits to stm32-devices
rm -r ../raw-device-data/stm32-devices
mkdir -p ../raw-device-data/stm32-devices
cp -r output/db/mcu ../raw-device-data/stm32-devices
cp -r output/db/plugins ../raw-device-data/stm32-devices

# cleanup
rm -r temp bin output
