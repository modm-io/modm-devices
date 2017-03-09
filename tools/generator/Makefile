
all: extract-stm32-data generate-avr generate-stm32

generate-avr:
	rm ../../devices/avr/*
	./avr_generator.py AT90
	./avr_generator.py ATtiny
	./avr_generator.py ATmega
	./avr_generator.py ATxmega

generate-stm32:
	rm ../../devices/stm32/*
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
	./stm_generator.py STM32L4+

extract-data-stm32:
	(cd raw-data-extractor && ./extract-stm32.sh)

extract-data-avr:
	(cd raw-data-extractor && ./extract-avr.sh)
