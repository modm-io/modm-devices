# Copyright (c) 2026, Niklas Hauser
# All rights reserved.
#
# The device data is extracted by the pipelines of modm-data, which must be
# installed together with its input sources, see:
# https://github.com/modm-io/modm-data

.PHONY: test
test:
	@python3 -m unittest discover -p "*_test.py"

# Generate a vendor (stm32, avr, sam, nrf, rp) or a device prefix (e.g. stm32f4)
.PHONY: generate-%
generate-%:
	@python3 -m dfg $(@:generate-%=%)
	@python3 ../scripts/sync_docs.py

.PHONY: generate
generate:
	@python3 -m dfg all
	@python3 ../scripts/sync_docs.py

.PHONY: sync_docs
sync_docs:
	@python3 ../scripts/sync_docs.py
