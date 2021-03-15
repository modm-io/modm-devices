
# Git Submodule management
ext/%:
	@git clone https://github.com/modm-io/$(@:ext/%=%).git $@

.PHONY: init
init: ext/cmsis-header-stm32 ext/cmsis-5-partial #ext/cmsis-header-sam

.PHONY: clean_init
clean_init:
	@rm -rf ext/

# Raw device data management
raw-device-data/%-devices:
	(cd raw-data-extractor && python3 extract-$(@:raw-device-data/%-devices=%).py)

.PHONY: extract
extract: raw-device-data/avr-devices raw-device-data/stm32-devices raw-device-data/sam-devices raw-device-data/nrf-devices

.PHONY: clean_extract
clean_extract:
	@rm -rf raw-device-data/

.PHONY: update-data-%
update-data-%:
	rm -rf $(@:update-data-%=raw-device-data/%-devices)
	@$(MAKE) $(@:update-data-%=raw-device-data/%-devices)

.PHONY: update-data
update-data: update-data-avr update-data-stm32 update-data-sam update-data-nrf

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

.PHONY: generate-sam
generate-sam: generate-saml21 generate-samd21 generate-samd51



# NRF device files
.PHONY: generate-nrf%
generate-nrf%: raw-device-data/nrf-devices ext/cmsis-5-partial
	@rm -f ../../devices/nrf/$(@:generate-%=%)*
	./nrf_generator.py $(@:generate-%=%)

.PHONY: generate-nrf
generate-nrf: generate-nrf52810 generate-nrf52811 generate-nrf52820 generate-nrf52832 generate-nrf52833 generate-nrf52840


# STM32 device files
.PHONY: generate-stm32%
generate-stm32%: raw-device-data/stm32-devices ext/cmsis-5-partial ext/cmsis-header-stm32
	@rm -f ../../devices/stm32/$(@:generate-%=%)*
	./stm_generator.py $(@:generate-%=%)

.PHONY: generate-stm32
generate-stm32: generate-stm32f0 generate-stm32f1 generate-stm32f2 generate-stm32f3 \
				generate-stm32f4 generate-stm32f7 generate-stm32g0 generate-stm32g4 \
				generate-stm32h7 generate-stm32l0 generate-stm32l1 generate-stm32l4 \
				generate-stm32wb generate-stm32wl
