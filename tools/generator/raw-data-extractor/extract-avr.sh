#!/usr/bin/env zsh

# devices to download
DEVICES=(
  ATtiny
  ATmega
  XMEGAA
  XMEGAB
  XMEGAC
  XMEGAD
  XMEGAE
)

# create temp dir
mkdir temp-avr
mkdir zips-avr
# create avr-devices folder
rm -r ../raw-device-data/avr-devices
mkdir -p ../raw-device-data/avr-devices

packurl="http://packs.download.atmel.com/"
packhtml=$(curl -s $packurl)

for ((i=1;i<=${#DEVICES[@]};++i)); do
    device=$(echo ${DEVICES[i]} | tr '[:upper:]' '[:lower:]')
    # download software
    atpack=$(echo $packhtml | ack -1 "data-link=\"(Atmel\.${DEVICES[i]}_DFP\..*?\.atpack)\"" --output "\$1")
    echo "Downloading ${atpack}..."
    curl -z zips-avr/${device}.zip -o zips-avr/${device}.zip ${packurl}${atpack}

    # extract in two steps
    echo "Extracting ${atpack}..."
    unzip -q zips-avr/${device}.zip -d temp-avr/${device}

    # move the juicy bits to avr-devices
    echo "Moving ${atpack}..."
    cp -r temp-avr/${device}/atdf ../raw-device-data/avr-devices/${device}
done

# cleanup
rm -r temp-avr
