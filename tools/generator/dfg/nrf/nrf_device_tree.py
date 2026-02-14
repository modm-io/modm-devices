# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, Niklas Hauser
# Copyright (c)      2016, Fabian Greif
# Copyright (c)      2020, Hannes Ellinger
# All rights reserved.

import math
import logging
import re
import os
from pathlib import Path
from lxml import etree

from ..device_tree import DeviceTree
from ..input.xml import XMLReader

from .nrf_identifier import NRFIdentifier

LOGGER = logging.getLogger('dfg.nrf.reader')

class NRFDeviceTree:
    """ NRFDeviceTree
    This NRF specific part description file reader knows the structure and
    translates the data into a platform independent format.
    """

    _pin_data_cache = {}

    @staticmethod
    def _text_lines(element):
        lines = [line.strip() for line in element.xpath('.//p[contains(@class, "lines")]/text()') if line.strip()]
        if lines:
            return lines
        return [line.strip() for line in element.xpath('.//text()') if line.strip()]

    @staticmethod
    def _parse_gpio_ref(token):
        if token is None:
            return None
        cleaned = token.strip().upper().rstrip('.,;:')
        if not cleaned.startswith('P') or '.' not in cleaned:
            return None

        body = cleaned[1:]
        port_text, pin_text = body.split('.', 1)
        if not port_text.isdigit():
            return None

        pin_digits = []
        for character in pin_text:
            if character.isdigit():
                pin_digits.append(character)
            else:
                break
        if not pin_digits:
            return None

        return str(int(port_text)), str(int(''.join(pin_digits)))

    @staticmethod
    def _extract_package_name(caption):
        compact = re.sub(r'\s+', ' ', caption or '').strip()
        match = re.search(r'(aQFN\d+|QFN\d+|WLCSP\d+|WLCSP)', compact, re.IGNORECASE)
        if match is not None:
            return match.group(1).replace('aqfn', 'aQFN').replace('wlcsp', 'WLCSP')
        return None

    @staticmethod
    def _extract_pin_refs(pin_text):
        text = pin_text or ''
        tokenized = text
        for separator in ('-', '/', ',', ';', ':', '(', ')', '[', ']'):
            tokenized = tokenized.replace(separator, f' {separator} ')

        refs = []
        for token in tokenized.split():
            ref = NRFDeviceTree._parse_gpio_ref(token)
            if ref is not None:
                refs.append(ref)
        if not refs:
            return []

        if len(refs) == 2 and '-' in text:
            first_port, first_pin = refs[0][0], int(refs[0][1])
            second_port, second_pin = refs[1][0], int(refs[1][1])
            if first_port == second_port and first_pin <= second_pin:
                return [(first_port, str(pin)) for pin in range(first_pin, second_pin + 1)]

        unique = []
        for value in refs:
            if value not in unique:
                unique.append(value)
        return unique

    @staticmethod
    def _extract_special_tags(text):
        lower = text.lower()
        tags = set()

        for ain in re.findall(r'ain\s*(\d+)', lower):
            tags.add(f'ain{ain}')

        if 'trace' in lower:
            tags.add('trace')
        if 'traceclk' in lower:
            tags.add('traceclk')
        for tracedata in re.findall(r'tracedata\s*\[?(\d+)\]?', lower):
            tags.add(f'tracedata{tracedata}')
        if 'serial wire output' in lower or re.search(r'\bswo\b', lower):
            tags.add('swo')

        if 'qspi' in lower:
            tags.add('qspi')
            for signal in re.findall(r'\b(io[0-3]|sck|csn|dcx)\s+for\s+qspi\b', lower):
                tags.add(f'qspi_{signal}')
            for signal in re.findall(r'qspi\s*/\s*(csn|sck)\b', lower):
                tags.add(f'qspi_{signal}')

        if 'spim4' in lower:
            tags.add('spim4')
            for signal in re.findall(r'\b(sck|mosi|miso|csn|dcx)\s+for\s+spim4\b', lower):
                tags.add(f'spim4_{signal}')

        if 'twim' in lower:
            tags.add('twim')
        if 'twis' in lower:
            tags.add('twis')
        if re.search(r'\btwi\b', lower):
            tags.add('twi')

        return tags

    @staticmethod
    def _pin_data_from_html(did):
        product = f"nrf{did.family}{did.series}"
        if product in NRFDeviceTree._pin_data_cache:
            return NRFDeviceTree._pin_data_cache[product]

        raw_data_root = Path(__file__).resolve().parents[2] / 'raw-device-data' / 'nrf-devices'
        html_file = raw_data_root / f'ps_{product}-pin.html'
        result = {'packages': [], 'specials': {}}
        if not html_file.exists():
            NRFDeviceTree._pin_data_cache[product] = result
            return result

        try:
            tree = etree.parse(str(html_file), parser=etree.HTMLParser(recover=True))
        except Exception as error:
            LOGGER.warning("Failed to parse Nordic pin file '%s': %s", html_file.name, error)
            NRFDeviceTree._pin_data_cache[product] = result
            return result

        package_pinouts = []
        special_tags = {}

        for table in tree.xpath('//table[caption]'):
            caption_parts = [text.strip() for text in table.xpath('./caption//text()') if text.strip()]
            caption_text = ' '.join(caption_parts)
            caption_lower = caption_text.lower()

            if 'special gpio considerations' in caption_lower:
                for row in table.xpath('./tbody/tr'):
                    cells = row.xpath('./td')
                    if len(cells) < 2:
                        continue
                    pin_text = ' '.join(NRFDeviceTree._text_lines(cells[0]))
                    description = ' '.join(NRFDeviceTree._text_lines(cells[1]))
                    refs = NRFDeviceTree._extract_pin_refs(pin_text)
                    tags = NRFDeviceTree._extract_special_tags(description)
                    for ref in refs:
                        special_tags.setdefault(ref, set()).update(tags)
                continue

            if 'pin assignment' not in caption_lower and 'ball assignment' not in caption_lower:
                continue

            package_name = NRFDeviceTree._extract_package_name(caption_text)
            if package_name is None:
                context_parts = [
                    text.strip()
                    for text in table.xpath('ancestor::article[1]/@id | ancestor::article[1]/h2[1]//text()')
                    if text.strip()
                ]
                package_name = NRFDeviceTree._extract_package_name(' '.join(context_parts))
            if package_name is None:
                continue

            headers = []
            for header_cell in table.xpath('./thead//th'):
                header_text = ' '.join([text.strip() for text in header_cell.xpath('.//text()') if text.strip()]).lower()
                if header_text:
                    headers.append(header_text)
            if not headers:
                continue

            pin_idx = None
            name_idx = None
            function_idx = None
            description_idx = None
            recommended_idx = None
            for index, header in enumerate(headers):
                if pin_idx is None and header == 'pin':
                    pin_idx = index
                elif name_idx is None and header == 'name':
                    name_idx = index
                elif function_idx is None and 'function' in header:
                    function_idx = index
                elif description_idx is None and 'description' in header:
                    description_idx = index
                elif recommended_idx is None and 'recommended' in header:
                    recommended_idx = index
            if pin_idx is None or name_idx is None:
                continue

            package_pins = []
            for row in table.xpath('./tbody/tr'):
                cells = row.xpath('./td')
                if len(cells) <= max(pin_idx, name_idx):
                    continue

                pin_position = ' '.join(NRFDeviceTree._text_lines(cells[pin_idx]))
                name_lines = NRFDeviceTree._text_lines(cells[name_idx])
                if not pin_position or not name_lines:
                    continue

                gpio_match = None
                for line in name_lines:
                    parsed_ref = NRFDeviceTree._parse_gpio_ref(line)
                    if parsed_ref is not None:
                        gpio_match = (parsed_ref[0], parsed_ref[1], f"P{int(parsed_ref[0])}.{int(parsed_ref[1]):02d}")
                        break

                pin_name = gpio_match[2] if gpio_match is not None else name_lines[0]
                function_text = ' '.join(NRFDeviceTree._text_lines(cells[function_idx])) if function_idx is not None and function_idx < len(cells) else ''
                description_text = ' '.join(NRFDeviceTree._text_lines(cells[description_idx])) if description_idx is not None and description_idx < len(cells) else ''
                recommended_text = ' '.join(NRFDeviceTree._text_lines(cells[recommended_idx])) if recommended_idx is not None and recommended_idx < len(cells) else ''

                pin_entry = {'position': pin_position, 'name': pin_name}
                if gpio_match is None and 'power' in function_text.lower():
                    pin_entry['type'] = 'power'
                package_pins.append(pin_entry)

                if gpio_match is not None:
                    row_text = ' '.join(name_lines + [function_text, description_text, recommended_text])
                    tags = NRFDeviceTree._extract_special_tags(row_text)
                    if tags:
                        ref = (gpio_match[0], gpio_match[1])
                        special_tags.setdefault(ref, set()).update(tags)

            if package_pins:
                package_pinouts.append({'name': package_name, 'pins': package_pins})

        result = {
            'packages': package_pinouts,
            'specials': {f"{port}.{pin}": sorted(list(tags)) for (port, pin), tags in special_tags.items() if tags}
        }
        NRFDeviceTree._pin_data_cache[product] = result
        return result

    @staticmethod
    def _resolve_pin_special_signals(pin_specials, signals_per_driver):
        resolved = {}
        consumed_driver_signals = set()

        for pin_key, tags in pin_specials.items():
            pin_signals = []
            seen = set()

            for tag in tags:
                if tag in ('spim4', 'qspi', 'trace'):
                    continue

                entries = []
                if tag.startswith('spim4_'):
                    entries.append({'driver': 'spim', 'instance': '4', 'name': tag.split('_', 1)[1]})
                elif tag.startswith('qspi_'):
                    entries.append({'driver': 'qspi', 'name': tag.split('_', 1)[1]})
                elif tag == 'traceclk':
                    entries.append({'driver': 'trace', 'name': 'clk'})
                elif tag.startswith('tracedata'):
                    entries.append({'driver': 'trace', 'name': tag.replace('tracedata', 'data', 1)})
                elif tag == 'swo':
                    entries.append({'driver': 'trace', 'name': 'swo'})
                elif tag in ('twi', 'twim', 'twis'):
                    for driver in ('twim', 'twis', 'twi'):
                        if driver not in signals_per_driver:
                            continue
                        for signal_name in ('scl', 'sda'):
                            if signal_name in signals_per_driver[driver]:
                                entries.append({'driver': driver, 'name': signal_name})
                elif re.fullmatch(r'ain\d+', tag):
                    for driver, names in signals_per_driver.items():
                        if tag in names:
                            entries.append({'driver': driver, 'name': tag})
                            consumed_driver_signals.add((driver, tag))
                else:
                    entries.append({'driver': 'special', 'name': tag})

                for entry in entries:
                    key = (entry.get('driver'), entry.get('instance', ''), entry.get('name'))
                    if key in seen:
                        continue
                    seen.add(key)
                    pin_signals.append(entry)

            if pin_signals:
                resolved[pin_key] = pin_signals

        return resolved, consumed_driver_signals

    @staticmethod
    def _properties_from_file(ld_filename):
        p = {}

        partname = ld_filename.split('/')[-1]
        partname = partname.split('.')[0]
        partname = partname.replace('_', '-')

        did = NRFIdentifier.from_string(partname.lower())
        p['id'] = did

        xml_filename = re.sub(r'\_\w{4}(\_\w+)?.ld', r'\1.svd', ld_filename)
        xml_path = Path(xml_filename)
        if not xml_path.exists():
            fallback_svd = {
                "51": "nrf51.svd",
                "52": "nrf52.svd",
            }.get(did.family)
            if fallback_svd is not None:
                candidate = Path(ld_filename).with_name(fallback_svd)
                if candidate.exists():
                    xml_path = candidate
        device_file = XMLReader(str(xml_path))

        LOGGER.info("Parsing '%s'", did.string)

        # information about the core and architecture
        core = device_file.query("//device/cpu/name")[0].text.lower().replace("cm", "cortex-m")
        if device_file.query("//device/cpu/fpuPresent")[0].text in ('1', 'true'):
            p["fpu"] = "fpv4-sp-d16" if "m4" in core else "fpv5-sp-d16"
        p["core"] = core
        p["revision"] = device_file.query("//device/cpu/revision")[0].text


        # find the values for flash and ram
        memlines = []
        with open(ld_filename, 'r') as linkerfile:
            status = 0
            for line in linkerfile:
                if status == 0 and "MEMORY" in line:
                    status = 1
                elif status == 1 and "{" in line:
                    status = 2
                elif status == 2:
                    if "}" in line:
                        status = 3
                    else:
                        memlines.append(line)

        memories = []

        if did.family == "53":
            if did.core == "app":
                memories = [{"name": "flash", "access": "rx", "size": str(1024*1024), "start": "0x00000000"}]
                for idx in range(8):
                    memories.append({"name": f"ram{idx}", "access": "rwx", "size": str(64*1024), "start": hex(0x20000000 + idx * 64*1024)})
            else:
                memories = [{"name": "flash", "access": "rx", "size": str(256*1024), "start": "0x01000000"}]
                for idx in range(4):
                    memories.append({"name": f"ram{idx}", "access": "rwx", "size": str(16*1024), "start": hex(0x21000000 + idx * 16*1024)})
        else:
            for memline in memlines:
                matchString = r"  (?P<name>\w+) \((?P<access>\w+)\) : ORIGIN = (?P<start>0x[\da-fA-F]+), LENGTH = (?P<size>0x[\da-fA-F]+)"
                match = re.search(matchString, memline)
                name = match.group("name").lower()
                if "ext" in name:
                    continue
                name = name.replace("code_ram", "code")
                memories.append({
                    "name": name,
                    "access": match.group("access").lower(),
                    "size": str(int(match.group("size").lower(), 16)),
                    "start": match.group("start").lower()})

        p["memories"] = memories


        # Signals
        signals = {}
        for s in device_file.query("//peripherals/peripheral/registers/cluster"):
            if s.find('name').text == "PSEL":

                # find parent peripheral
                parent_peripheral_instance = s.getparent().getparent().find('name').text.lower().split('_')[0]
                signals[parent_peripheral_instance] = []

                # find all signals of peripheral
                signal_elements = s.findall('register/name')
                for signal_element in signal_elements:
                    signal_name = signal_element.text.lower()
                    signals[parent_peripheral_instance].append(signal_name)

        # nRF51 and older SVD files may use PSEL* registers directly instead of a PSEL cluster
        for peripheral in device_file.query("//peripherals/peripheral"):
            peripheral_name = peripheral.find('name').text.lower().split('_')[0]
            register_names = peripheral.findall('registers/register/name')
            for register_name in register_names:
                register_text = register_name.text
                if register_text is None or not register_text.startswith("PSEL"):
                    continue
                signal_name = register_text[4:].lower()
                if signal_name == "":
                    continue
                signals.setdefault(peripheral_name, [])
                if signal_name not in signals[peripheral_name]:
                    signals[peripheral_name].append(signal_name)


        # drivers and gpios
        raw_modules = device_file.query("//peripherals/peripheral")
        modules = []
        ports = {}
        gpios = []
        fixed_signals = {}
        for m in raw_modules:
            modulename = m.find('name').text
            if modulename.endswith("_S"): continue
            modulename = modulename.split('_')[0]
            moduledesc = m.find('description').text

            if "GPIO Port" in moduledesc or modulename == "GPIO":
                # omit the leading P of the port names, also of the derived ports
                portnumber = "0" if modulename == "GPIO" else modulename[1:]
                if m.get('derivedFrom') is not None:
                    portsize = ports[m.get('derivedFrom')[1:].split('_')[0]]
                else:
                    portsize = int(m.find('size').text, base=0)

                ports[portnumber] = portsize
                for i in range(portsize):
                    gpios.append((portnumber, str(i)))

            else:
                matchString = r"(?P<module>.*\D)(?P<instance>\d*$)"
                match = re.search(matchString, modulename)
                module = match.group("module").lower()
                modules.append({'module': module, 'instance': modulename.lower()})

                # copy available signals to all derived peripherals
                if m.get('derivedFrom') is not None:
                    if m.get('derivedFrom').lower() in signals:
                        LOGGER.debug(modulename.lower() + " is derived from " + m.get('derivedFrom').lower())
                        signals[modulename.lower()] = signals[m.get('derivedFrom').lower()]

                # extract fixed analog channel capabilities from enum descriptions (AIN0..AINx)
                for field in m.findall('registers//field'):
                    field_name = field.find('name')
                    if field_name is None or field_name.text is None:
                        continue
                    if field_name.text.upper() not in ('PSEL', 'PSELP', 'PSELN'):
                        continue
                    for enum_value in field.findall('enumeratedValues/enumeratedValue'):
                        enum_name = enum_value.find('name').text if enum_value.find('name') is not None else ''
                        enum_desc = enum_value.find('description').text if enum_value.find('description') is not None else ''
                        for token in (enum_name, enum_desc):
                            if token is None:
                                continue
                            match_ain = re.search(r'AIN(?P<index>\d+)', token.upper())
                            if match_ain is None:
                                continue
                            fixed_signals.setdefault(module, set()).add(f"ain{match_ain.group('index')}")
        p['modules'] = sorted(list(set([(m['module'], m['instance']) for m in modules])))
        p['gpios'] = gpios
        p['signals'] = []
        p['fixed_signals'] = {module: sorted(list(names)) for module, names in fixed_signals.items()}
        for instance in signals:
            for signal in signals[instance]:
                matchString = r"(?P<module>.*\D)(?P<instance>\d*$)"
                match = re.search(matchString, instance)
                if not "[%s]" in signal:  # TODO take care of multichannel signals like OUT[%s] of PWM peripheral
                    p['signals'].append({'driver': match.group("module").lower(), 'instance': instance, 'name': signal})

        pin_data = NRFDeviceTree._pin_data_from_html(did)
        p['pin_packages'] = pin_data['packages']
        p['pin_specials'] = pin_data['specials']


        interrupts = []
        raw_interrupt = device_file.query("//peripherals/peripheral/interrupt")
        for i in raw_interrupt:
            interruptname = i.find('name').text
            interruptnum = i.find('value').text
            interrupts.append({'position': interruptnum, 'name': interruptname})

        # Unique interrupts
        p['interrupts'] = []
        for interrupt in interrupts:
            if interrupt not in p['interrupts']:
                p['interrupts'].append(interrupt)

        LOGGER.debug("Found GPIOs: [%s]", ", ".join([p.upper() + "." + i for p,i in p['gpios']]))
        LOGGER.debug("Available Modules are:\n" + NRFDeviceTree._modulesToString(p['modules']))
        LOGGER.debug("Found Signals:")
        for sig in p['signals']:
            LOGGER.debug("    %s", sig)
        LOGGER.debug("Found Interrupts:")
        for intr in p['interrupts']:
            LOGGER.debug("    %s", intr)

        return p

    @staticmethod
    def _modulesToString(modules):
        string = ""
        mods = sorted(modules)
        char = mods[0][0][0:1]
        for module, instance in mods:
            if not instance.startswith(char):
                string += "\n"
            string += instance + " \t"
            char = instance[0][0:1]
        return string

    @staticmethod
    def _device_tree_from_properties(p):
        tree = DeviceTree('device')
        tree.ids.append(p['id'])

        def topLevelOrder(e):
            order = ['attribute-flash', 'attribute-ram', 'attribute-eeprom', 'attribute-core', 'attribute-mcu', 'header', 'attribute-define']
            if e.name in order:
                if e.name in ['attribute-flash', 'attribute-eeprom', 'attribute-ram']:
                    return (order.index(e.name), int(e['value']))
                else:
                    return (order.index(e.name), e['value'])
            return (len(order), -1)
        # tree.addSortKey(topLevelOrder)

        # NRFDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-flash')
        # NRFDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-ram')
        # NRFDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-eeprom')
        # NRFDeviceTree.addDeviceAttributesToNode(p, tree, 'attribute-mcu')

        def driverOrder(e):
            if e.name == 'driver':
                if e['name'] == 'core':
                    # place the core at the very beginning
                    return ('aaaaaaa', e['type'] + e.get('fpu', ''))
                if e['name'] == 'gpio':
                    # place the gpio at the very end
                    return ('zzzzzzz', e['type'])
                # sort remaining drivers by type and compatible strings
                return (e['name'], e['type'])
            return ("", "")
        tree.addSortKey(driverOrder)

        # Core
        core_child = tree.addChild('driver')
        core_child.setAttributes('name', 'core', 'type', p['core'])
        core_child.setAttributes(["fpu", "revision"], p)
        core_child.addSortKey(lambda e: (int(e['position']), e['name']) if e.name == 'vector' else (-1, ""))
        core_child.addSortKey(lambda e: (e['name'], int(e['size'])) if e.name == 'memory' else ("", -1))
        core_child.addSortKey(lambda e: (e.name, e["value"]) if e.name.startswith("attribute-") else ("", ""))

        for section in p["memories"]:
            memory_section = core_child.addChild("memory")
            memory_section.setAttributes(["name", "access", "start", "size"], section)
        # sort the node children by start address and size
        core_child.addSortKey(lambda e: (int(e["start"], 16), int(e["size"])) if e.name == "memory" else (-1, -1))

        # for memory in ['flash', 'ram', 'lpram', 'eeprom']:
        #     if memory not in p: continue;
        #     memory_section = core_child.addChild('memory')
        #     memory_section.setAttribute('name', memory)
        #     memory_section.setAttribute('size', p[memory])

        for vector in p['interrupts']:
            if int(vector['position']) < 0: continue;
            vector_section = core_child.addChild('vector')
            vector_section.setAttributes(['position', 'name'], vector)

        modules = {}
        for m, i in p['modules']:
            # filter out non-peripherals: fuses, micro-trace buffer
            if m in ['fuses', 'mtb', 'systemcontrol', 'systick', 'hmatrixb', 'hmatrix', 'approtect']: continue;
            if m not in modules:
                modules[m] = [i]
            else:
                modules[m].append(i)

        # for nRF5x, represent peripheral pin capabilities on the peripheral driver itself
        signals_per_driver = {}
        if p['id']['family'] in ('51', '52', '53'):
            for signal in p['signals']:
                name = signal['name']
                if 'index' in signal:
                    name += signal['index']
                signals_per_driver.setdefault(signal['driver'], set()).add(name)
            for driver, names in p.get('fixed_signals', {}).items():
                signals_per_driver.setdefault(driver, set()).update(names)

        resolved_pin_specials, consumed_driver_signals = NRFDeviceTree._resolve_pin_special_signals(
            p.get('pin_specials', {}),
            signals_per_driver,
        )
        for driver_name, signal_name in consumed_driver_signals:
            if driver_name in signals_per_driver:
                signals_per_driver[driver_name].discard(signal_name)


        compatible = p['id']['platform'] + p['id']['family']
        # add all other modules
        for name, instances in modules.items():
            driver = tree.addChild('driver')
            dtype = name

            driver.setAttributes('name', dtype, 'type', compatible)
            # Add all instances to this driver
            if any(i != dtype for i in instances):
                driver.addSortKey(lambda e: e['value'] if e.name == 'instance' else '')
                for i in instances:
                    inst = driver.addChild('instance')
                    inst.setValue(i[len(dtype):])

            if dtype in signals_per_driver:
                driver.addSortKey(lambda e: (e.get('name', '') or '') if e.name == 'signal' else '')
                for signal_name in sorted(signals_per_driver[dtype]):
                    signal_section = driver.addChild('signal')
                    signal_section.setAttribute('name', signal_name)

        # GPIO driver
        gpio_driver = tree.addChild('driver')
        gpio_driver.setAttributes('name', 'gpio', 'type', compatible)
        # gpio_driver.addSortKey(lambda e : (e['port'], int(e['pin'])))

        # add all signals
        if p['id']['family'] not in ('51', '52', '53'):
            for s in p['signals']:
                driver, instance, name = s['driver'], s['instance'], s['name']
                # add the af node
                gpio_signal = {'driver': driver}
                if instance != driver:
                    gpio_signal['instance'] = instance.replace(driver, '')
                if name != driver and name != 'int':
                    if 'index' in s: name += s['index'];
                    gpio_signal['name'] = name
                elif 'index' in s:
                    gpio_signal['name'] = s['index']
                if "name" not in gpio_signal:
                    LOGGER.error("%s has no name!", s)
                    continue

                af = gpio_driver.addChild('signal')
                af.setAttributes(['driver', 'instance', 'name'], gpio_signal)
                af.addSortKey(lambda e: (e['driver'],
                                         int(e.get('instance', '-1')),
                                         e.get('name', '')))

        # add all GPIOs
        gpio_nodes = {}
        for port, pin in p['gpios']:
            pin_driver = gpio_driver.addChild('gpio')
            pin_driver.setAttributes('port', port, 'pin', pin)
            gpio_nodes[f"{port}.{pin}"] = pin_driver

        for pin_key, signals in resolved_pin_specials.items():
            gpio_node = gpio_nodes.get(pin_key)
            if gpio_node is None:
                continue
            for signal in signals:
                special_signal = gpio_node.addChild('signal')
                special_signal.setAttributes(['driver', 'instance', 'name'], signal)

        for package in p.get('pin_packages', []):
            package_node = gpio_driver.addChild('package')
            package_node.setAttribute('name', package['name'])
            for package_pin in package['pins']:
                pin_node = package_node.addChild('pin')
                pin_node.setAttributes(['position', 'name', 'type'], package_pin)

        return tree

    @staticmethod
    def addDeviceAttributesToNode(p, node, name):
        pname = name.split('-')[-1]
        if pname not in p: return;
        props = p[pname]
        if not isinstance(props, list):
            props = [props]
        for prop in props:
            child = node.addChild(name)
            child.setValue(prop)

    @staticmethod
    def from_file(filename):
        p = NRFDeviceTree._properties_from_file(str(filename))
        if p is None: return None;
        return NRFDeviceTree._device_tree_from_properties(p)
