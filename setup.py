#!/usr/bin/env python

from distutils.core import setup

setup(name='delicious2fluid',
      version='0.1.2',
      description="Imports delicious bookmarks to FluidDB",
      author='Nicholas Tollervey',
      author_email='ntoll@ntoll.org',
      url='http://fluidinfo.com',
      license='MIT',
      requires=['httplib2', ],
      scripts=['bin/delicious2fluid', ],
      py_modules=['delicious2fluid', ],
      long_description=open('README.rst').read(),
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Database',
                   'Topic :: Internet :: WWW/HTTP',
                   'Topic :: Software Development :: Libraries'])
