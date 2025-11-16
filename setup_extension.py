
from setuptools import setup, Extension

module = Extension('example_extension',
                   sources=['example_extension.c'],
                   extra_compile_args=['-g', '-O2'])

setup(
    name='example_extension',
    ext_modules=[module]
)
