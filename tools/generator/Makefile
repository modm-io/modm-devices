
init:
	@git clone https://github.com/modm-io/cmsis-header-stm32.git ext/cmsis-header-stm32
	@git clone https://github.com/modm-io/cmsis-5-partial.git ext/cmsis-5-partial


extract-avr:
	(cd raw-data-extractor && python3 extract-avr.py)

extract-stm32:
	(cd raw-data-extractor && python3 extract-stm32.py)


generate-at90:
	@rm -f ../../devices/avr/at90*
	./avr_generator.py AT90

generate-attiny:
	@rm -f ../../devices/avr/attiny*
	./avr_generator.py ATtiny

generate-atmega:
	@rm -f ../../devices/avr/atmega*
	./avr_generator.py ATmega

generate-avr: generate-at90 generate-attiny generate-atmega


generate-stm32f0:
	@rm -f ../../devices/stm32/stm32f0*
	./stm_generator.py STM32F0

generate-stm32g0:
	@rm -f ../../devices/stm32/stm32g0*
	./stm_generator.py STM32G0

generate-stm32f1:
	@rm -f ../../devices/stm32/stm32f1*
	./stm_generator.py STM32F1

generate-stm32f2:
	@rm -f ../../devices/stm32/stm32f2*
	./stm_generator.py STM32F2

generate-stm32f3:
	@rm -f ../../devices/stm32/stm32f3*
	./stm_generator.py STM32F3

generate-stm32f4:
	@rm -f ../../devices/stm32/stm32f4*
	./stm_generator.py STM32F4

generate-stm32f7:
	@rm -f ../../devices/stm32/stm32f7*
	./stm_generator.py STM32F7

generate-stm32h7:
	@rm -f ../../devices/stm32/stm32h7*
	./stm_generator.py STM32H7

generate-stm32l0:
	@rm -f ../../devices/stm32/stm32l0*
	./stm_generator.py STM32L0

generate-stm32l1:
	@rm -f ../../devices/stm32/stm32l1*
	./stm_generator.py STM32L1

generate-stm32l4:
	@rm -f ../../devices/stm32/stm32l4*
	./stm_generator.py STM32L4

generate-stm32: generate-stm32f0 generate-stm32g0 generate-stm32f1 generate-stm32f2 generate-stm32f3 generate-stm32f4 generate-stm32f7 generate-stm32h7 generate-stm32l0 generate-stm32l1 generate-stm32l4


.PHONY:
	init extract-avr extract-stm32
	generate-avr generate-at90 generate-attiny generate-atmega
	generate-stm32 generate-stm32f0 generate-stm32g0 generate-stm32f1 generate-stm32f2 generate-stm32f3
	generate-stm32f4 generate-stm32f7 generate-stm32h7 generate-stm32l0 generate-stm32l1 generate-stm32l4