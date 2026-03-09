
# Git Submodule management
ext/STM32F1xx_DFP:
	@$(eval PACKURL=$(shell curl -s "https://www.keil.arm.com/packs/?q=$(@:ext/%=%)" | grep -oE "https://www.keil.com/pack/.*?\.pack" | head -n 1))
	@curl -Ls "${PACKURL}" -o $@.zip
	@unzip -q $@.zip -d $@
	@rm $@.zip

ext/STM32%_DFP:
	@git clone https://github.com/Open-CMSIS-Pack/$(@:ext/%=%).git $@

ext/%:
	@git clone https://github.com/modm-io/$(@:ext/%=%).git $@

ext/stm32-cube-hal-drivers:
	@git clone https://github.com/modm-ext/stm32-cube-hal-drivers.git $@

ext/nrfx:
	@git clone https://github.com/nordicsemiconductor/nrfx.git $@

.PHONY: init
init: \
	ext/cmsis-header-stm32 ext/cmsis-5-partial ext/stm32-cube-hal-drivers \
	ext/STM32C0xx_DFP ext/STM32F0xx_DFP ext/STM32F1xx_DFP ext/STM32F2xx_DFP \
	ext/STM32F3xx_DFP ext/STM32F4xx_DFP ext/STM32F7xx_DFP ext/STM32G0xx_DFP \
	ext/STM32G4xx_DFP ext/STM32H5xx_DFP ext/STM32H7RSxx_DFP ext/STM32H7xx_DFP \
	ext/STM32L0xx_DFP ext/STM32L1xx_DFP ext/STM32L4xx_DFP ext/STM32L5xx_DFP \
	ext/STM32N6xx_DFP ext/STM32U0xx_DFP ext/STM32U3xx_DFP ext/STM32U5xx_DFP \
	ext/STM32WB0x_DFP ext/STM32WBAxx_DFP ext/STM32WBxx_DFP ext/STM32WL3x_DFP \
	ext/STM32WLxx_DFP

.PHONY: clean_init
clean_init:
	@rm -rf ext/

.PHONY: update_init
update_init: clean_init
	@$(MAKE) init

.PHONY: sync_docs
sync_docs:
	@python3 ../scripts/sync_docs.py


# Raw device data management
raw-device-data/%-devices:
	(cd raw-data-extractor && python3 extract-$(@:raw-device-data/%-devices=%).py)

.PHONY: extract
extract: raw-device-data/avr-devices raw-device-data/stm32-devices \
			raw-device-data/sam-devices raw-device-data/nrf-devices \
			raw-device-data/rp-devices

.PHONY: clean_extract
clean_extract:
	@rm -rf raw-device-data/

.PHONY: update-data-%
update-data-%: update_init
	rm -rf $(@:update-data-%=raw-device-data/%-devices)
	@$(MAKE) $(@:update-data-%=raw-device-data/%-devices)


.PHONY: update-data
update-data: update-data-avr update-data-stm32 update-data-sam \
				update-data-nrf update-data-rp


# AVR device files
.PHONY: generate-at%
generate-at%: raw-device-data/avr-devices
	@rm -f ../../devices/avr/$(@:generate-%=%)*
	./avr_generator.py $(@:generate-at%=%)

.PHONY: generate-avr
generate-avr: generate-at90 generate-attiny generate-atmega


# SAM device files
.PHONY: generate-sam%
generate-sam%: raw-device-data/sam-devices ext/cmsis-5-partial
	@rm -f ../../devices/sam/$(@:generate-%=%)*
	./sam_generator.py $(@:generate-%=%)

.PHONY: generate-samd5x-e5x
generate-samd5x-e5x: raw-device-data/sam-devices ext/cmsis-5-partial
	@rm -f ../../devices/sam/samd5*
	@rm -f ../../devices/sam/same5*
	./sam_generator.py samd5 same5

.PHONY: generate-samx7x
generate-samx7x: raw-device-data/sam-devices ext/cmsis-5-partial
	@rm -f ../../devices/sam/sam*7*
	./sam_generator.py same7 sams7 samv7

.PHONY: generate-sam
generate-sam:	generate-samda generate-samd1 generate-samd2 generate-samd09 \
				generate-saml2 generate-samg5 generate-samd5x-e5x generate-samx7x

# NRF device files
.PHONY: generate-nrf%
generate-nrf%: raw-device-data/nrf-devices ext/cmsis-5-partial ext/nrfx
	@rm -f ../../devices/nrf/$(@:generate-%=%)*
	./nrf_generator.py $(@:generate-%=%)

.PHONY: generate-nrf
generate-nrf:	generate-nrf51 generate-nrf52 generate-nrf53


# STM32 device files
.PHONY: generate-stm32%
generate-stm32%: raw-device-data/stm32-devices init
	@rm -f ../../devices/stm32/$(@:generate-%=%)*
	./stm_generator.py $(@:generate-%=%)

.PHONY: generate-stm32
generate-stm32: generate-stm32f0 generate-stm32f1 generate-stm32f2 generate-stm32f3 \
				generate-stm32f4 generate-stm32f7 generate-stm32c0 generate-stm32g0 \
				generate-stm32g4 generate-stm32h5 generate-stm32h7 generate-stm32l0 \
				generate-stm32l1 generate-stm32l4 generate-stm32l5 generate-stm32u0 \
				generate-stm32u3 generate-stm32u5 generate-stm32wb generate-stm32wl


# RP device files
.PHONY: generate-rp%
generate-rp%: raw-device-data/rp-devices
	@rm -f ../../devices/rp/$(@:generate-%=%)*
	./rp_generator.py $(@:generate-%=%)

.PHONY: generate-rp
generate-rp: generate-rp2040 generate-rp2350
