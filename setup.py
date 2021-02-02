# License: GPLv3

from os.path import realpath, dirname, join
from setuptools import setup, find_packages
import Arduinopydaqs

VERSION = Arduinopydaqs.__version__
PROJECT_ROOT = dirname(realpath(__file__))

REQUIREMENTS_FILE = join(PROJECT_ROOT, 'requirements.txt')

with open(REQUIREMENTS_FILE) as f:
    install_reqs = f.read().splitlines()

install_reqs.append('setuptools')

setup(name = "Arduinopydaqs",
      version=VERSION,
      description = " Arduino PEMG DAQ wrappers for axopy.",
      author = "Hancong Wu",
      author_email = "simoncong000@gmail.com",
      url = "https://github.com/HansNg18/Arduinopydaqs",
      packages=find_packages(),
      package_data={'': ['LICENSE.txt',
                         'README.md',
                         'requirements.txt']
                    },
      include_package_data=True,
      install_requires=install_reqs,
      license='GPLv3',
      platforms='any',
      long_description="""
Wrapper functions for Arduino PEMG DAQ packages and libraries in Python.
Mainly intended for internal use within IntellSensing Lab and Edinburgh 
Neuroprosthetics.
""")
