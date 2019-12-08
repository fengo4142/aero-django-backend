import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='pulpo-forms',
    version='1.1',
    packages=['pulpo_forms'],
    include_package_data=True,
    license='Apache License',
    description='Python module to create and validate forms from a schema',
    long_description=README,
    keywords='Python Survey Framework',
    url='https://github.com/pulpocoders/pulpo-forms-django',
    author='Octobot',
    author_email='info@trea.uy',
    zip_safe=True,
    install_requires=[],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Information Technology',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
    ],
)
