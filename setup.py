from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

setup(
    name = "modm-devices",
    version = "0.1.1",
    python_requires=">=3.5.0",
    packages = find_packages(exclude=["test"]),
    package_data = {
        "": ["resources/devices/*/*.xml",
             "resources/*",
             "resources/*/*"],
    },

    install_requires = ["lxml"],

    # Metadata
    author = "Niklas Hauser, Fabian Greif",
    author_email = "niklas@salkinium.com, fabian.greif@rwth-aachen.de",
    description = "Curated data for AVR and ARM Cortex-M devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license = "MPL-2.0",
    keywords = "modm lbuild modm-devices stm32 avr sam nrf",
    url = "https://github.com/modm-io/modm-devices",
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Topic :: Database",
        "Topic :: Software Development",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Embedded Systems",
    ],
)
