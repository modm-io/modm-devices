
init:
	@git clone https://github.com/modm-io/cmsis-header-stm32.git ext/cmsis-header-stm32
	@git clone https://github.com/modm-io/cmsis-5-partial.git ext/cmsis-5-partial


extract-data-avr:
	(cd raw-data-extractor && python3 extract-avr.py)

extract-data-stm32:
	(cd raw-data-extractor && python3 extract-stm32.py)


generate-avr:
	@rm -f ../../devices/avr/*
	./avr_generator.py AT90
	./avr_generator.py ATtiny
	./avr_generator.py ATmega

generate-avr-async:
	@rm -f ../../devices/avr/*
	./avr_generator.py AT90 &
	./avr_generator.py ATtiny &
	./avr_generator.py ATmega &


generate-stm32:
	@rm -f ../../devices/stm32/*
	./stm_generator.py STM32F0
	./stm_generator.py STM32F1
	./stm_generator.py STM32F2
	./stm_generator.py STM32F3
	./stm_generator.py STM32F4
	./stm_generator.py STM32F7
	./stm_generator.py STM32H7
	./stm_generator.py STM32L0
	./stm_generator.py STM32L1
	./stm_generator.py STM32L4

generate-stm32-async:
	@rm -f ../../devices/stm32/*
	./stm_generator.py STM32F0 &
	./stm_generator.py STM32F1 &
	./stm_generator.py STM32F2 &
	./stm_generator.py STM32F3 &
	./stm_generator.py STM32F4 &
	./stm_generator.py STM32F7 &
	./stm_generator.py STM32H7 &
	./stm_generator.py STM32L0 &
	./stm_generator.py STM32L1 &
	./stm_generator.py STM32L4 &


.PHONY:
	init
	extract-data-avr extract-data-stm32
	generate-avr generate-stm32
	generate-avr-async generate-stm32-async