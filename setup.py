#!/usr/bin/env python
# http://docs.python.org/distutils/setupscript.html
# http://docs.python.org/2/distutils/examples.html
# https://packaging.python.org/
# https://packaging.python.org/tutorials/distributing-packages/
from setuptools import setup, find_packages
import re
import os
from codecs import open


name = "mister"
kwargs = {}

def read(path):
    if os.path.isfile(path):
        with open(path, encoding='utf-8') as f:
            return f.read()
    return ""


vpath = os.path.join(name, "__init__.py")
if os.path.isfile(vpath):
    kwargs["packages"] = find_packages()
else:
    vpath = "{}.py".format(name)
    kwargs["py_modules"] = [name]
version = re.search(r"^__version__\s*=\s*[\'\"]([^\'\"]+)", read(vpath), flags=re.I | re.M).group(1)


long_description = read('README.rst')

tests_modules = [
    "testdata",
]
install_modules = []


setup(
    name=name,
    version=version,
    description='Approachable map/reduce jobs',
    long_description=long_description,
    author='Jay Marcyes',
    author_email='jay@marcyes.com',
    url='http://github.com/Jaymon/{}'.format(name),
    #py_modules=[name], # files
    #packages=find_packages(), # folders
    license="MIT",
    install_requires=install_modules,
    tests_require=tests_modules,
    classifiers=[ # https://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
#     entry_points = {
#         'console_scripts': [
#             '{} = {}:console'.format(name, name),
#         ],
#     }
    **kwargs
)

