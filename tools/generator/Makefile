
# Git Submodule management
ext/%:
	@git clone https://github.com/modm-io/$(@:ext/%=%).git $@

ext/stm32-cube-hal-drivers:
	@git clone https://github.com/modm-ext/stm32-cube-hal-drivers.git $@

.PHONY: init
init: ext/cmsis-header-stm32 ext/cmsis-5-partial ext/stm32-cube-hal-drivers #ext/cmsis-header-sam

.PHONY: clean_init
clean_init:
	@rm -rf ext/


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
update-data-%:
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
generate-nrf%: raw-device-data/nrf-devices ext/cmsis-5-partial
	@rm -f ../../devices/nrf/$(@:generate-%=%)*
	./nrf_generator.py $(@:generate-%=%)

.PHONY: generate-nrf
generate-nrf: generate-nrf52810 generate-nrf52811 generate-nrf52820 generate-nrf52832 generate-nrf52833 generate-nrf52840


# STM32 device files
.PHONY: generate-stm32%
generate-stm32%: raw-device-data/stm32-devices ext/cmsis-5-partial ext/cmsis-header-stm32 ext/stm32-cube-hal-drivers
	@rm -f ../../devices/stm32/$(@:generate-%=%)*
	./stm_generator.py $(@:generate-%=%)

.PHONY: generate-stm32
generate-stm32: generate-stm32f0 generate-stm32f1 generate-stm32f2 generate-stm32f3 \
				generate-stm32f4 generate-stm32f7 generate-stm32c0 generate-stm32g0 \
				generate-stm32g4 generate-stm32h5 generate-stm32h7 generate-stm32l0 \
				generate-stm32l1 generate-stm32l4 generate-stm32l5 generate-stm32u0 \
				generate-stm32u5 generate-stm32wb generate-stm32wl


# RP device files
.PHONY: generate-rp%
generate-rp%: raw-device-data/rp-devices
	@rm -f ../../devices/rp/$(@:generate-%=%)*
	./rp_generator.py $(@:generate-%=%)

.PHONY: generate-rp
generate-rp: generate-rp2040 generate-rp2350
