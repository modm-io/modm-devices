# Curated data for AVR and STM32 devices

This repository contains tools for extracting data from vendor sources,
filtering and reformatting them into a vendor-independent format.

This data is used by [the modm project][modm-io] to generate
its Hardware Abstraction Layer (HAL), startup code and additional support tools.
Please have a look [at modm's platform modules][modm-platform] for examples on
how to use this data.

These tools and this data set is maintained and curated by
[@salkinium][] only at [modm-io/modm-devices][modm-devices].
It is licensed under the MPLv2 license.

Currently data for <!--devicecount-->3666<!--/devicecount--> devices is available.
Please open an issue or better yet a pull request for additional support.

<!--devicetable-->
| Family        | Devices | Family        | Devices | Family        | Devices |
|:--------------|:--------|:--------------|:--------|:--------------|:--------|
| AT90          |    12   | ATMEGA        |   352   | ATTINY        |   148   |
| NRF52         |     7   | SAMD          |   209   | SAMG          |    10   |
| SAML          |    47   | SAMV          |    20   | STM32F0       |   169   |
| STM32F1       |   194   | STM32F2       |    71   | STM32F3       |   145   |
| STM32F4       |   347   | STM32F7       |   183   | STM32G0       |   243   |
| STM32G4       |   311   | STM32H7       |   208   | STM32L0       |   333   |
| STM32L1       |   142   | STM32L4       |   404   | STM32U5       |    47   |
| STM32WB       |    37   | STM32WL       |    27   |
<!--/devicetable-->


### TL;DR

```sh
git clone https://github.com/modm-io/modm-devices.git
cd modm-devices/tools/generator
# Generate STM32 device data
make generate-stm32
# Generate SAM device data
make generate-sam
# Generate AVR device data
make generate-avr
```

You need Python3 with lxml, jinja2, deepdiff and CppHeaderParser packages.

```sh
pip install lxml jinja2 deepdiff CppHeaderParser
```


### Background

The device data idea originally comes from [xpcc](http://xpcc.io), which is the
predecessor to modm. Around 2013 we wanted to remove some of the repetitive
steps for building a HAL for AVR and STM32 devices and we chose to extract some
common data and collapse some peripheral drivers into Jinja2 templates.

This eventually evolved from manually extracted device data to fully generated
device data as soon as we found machine readable data sources from vendors.
For AVRs, we use the Atmel Target Description Files and for STM32, we use
internal data extracted from the CubeMX code generator.

Thus the Device File Generator (DFG) was born. The DFG has been rewritten for
modm to make it more maintainable and flexible as well as handling edge cases
much better.

We've separated the device data from modm, so that it becomes easier for YOU
to use this data for your own purposes.
[I've written an blog post with all the details](http://blog.salkinium.com/modm-devices).


### Data quality

The quality of the resulting device data obviously depend heavily on the quality
of the input data. I reluctantly maintain [a manual patch list][patches] for the bugs I've
encountered in the vendor sources, that I don't want to write a fix for in the DFG.
I have sent some of these patches to a contact in ST, however, every new release
of CubeMX changes a lot of data and can reintroduce some of these bugs.
I don't have a contact at Atmel to send bug reports to.

In addition, the CubeMX and AVR data does not contain some very important
information, which has to be assembled manually from hundreds of datasheets and
is then injected into the DFG. This is extremely labor intensive.

Please be respectful in asking for more data: I do not like spending hours
upon hours copying this additional data out of datasheets. It's also much more
likely to introduce errors, so automating data extraction is much easier for me
to maintain. You may of course open an issue about wrong data, but I'd prefer if
you opened a pull request that fixes the problem in the DFG instead.

All fixes MUST BE REPRODUCIBLE by the DFG! This means you need to track down the
bug to either the raw vendor data (=> update the manual patches) or in the DFG
data pipeline (=> fix the DFG).

*DO NOT UNDER ANY CIRCUMSTANCES PUBLISH THE RAW DATA EXTRACTED FROM CUBEMX ANYWHERE!*
It is subject to ST's copyright and you are not allowed to distribute it!


### Data format

I initially wanted to format this data as [device trees][device-tree],
however, since it is so tied to the Linux kernel, there isn't (or wasn't) much
tool support available at the time (though now there is a Python parser in Zephyr),
so we wrote our own tree-based format, which we called "device files" since we're
so creative. It allows lossless overlaying of data trees to reduce the amount of
duplicate data noise which makes it easier to comprehend as a human.

I do not intend to standardize this **format**, it may change at any time for any
reason. This allows us maximum flexibility in encoding this complicated
device information. If you want to engage in format discussions, please consider
contributing to the device tree specification instead.

Since I may change this data format to accommodate new data, you should write your
**own formatter** of this data, so that you have much better control over what
your tools are expecting!
So, if you need this data in the form of a Device Tree, please write your own
data converter and maintain it yourself!

For modm we convert this format to a Python dictionary tree, for details see the
`DeviceFile` class in `tools/device/modm/device_file.py`.


[modm-talk-preview]: https://gist.githubusercontent.com/salkinium/43a303c61b5e15e9a91d34116ea5d07c/raw/ab836c051039421e7bb0875ec9cb93c2d3f76236/modm-devices.png
[modm-talk]: http://salkinium.com/talks/modm_embo17.pdf
[modm-platform]: https://github.com/modm-io/modm/tree/develop/src/modm/platform
[device-tree]: https://www.devicetree.org
[@salkinium]: http://github.com/salkinium
[modm-devices]: https://github.com/modm-io/modm-devices
[modm-io]: https://github.com/modm-io
[patches]: https://github.com/modm-io/modm-devices/tree/develop/tools/generator/raw-data-extractor/patches
