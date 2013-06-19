#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import cherrybase

def main ():
    setup (
        name = 'cherrybase',
        version = cherrybase.__version__,
        description = 'Wrapper around CherryPy',
        long_description = 'Wrapper around CherryPy',
        classifiers = [
            'Development Status :: 5 - Production/Stable',
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: Freely Distributable',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.3',
            'Programming Language :: Python :: 2.4',
            'Programming Language :: Python :: 2.5',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Topic :: Internet :: WWW/HTTP',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
            'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
            'Topic :: Internet :: WWW/HTTP :: WSGI',
            'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
            'Topic :: Software Development :: Libraries :: Application Frameworks',
        ],
        author = 'Ruslan V. Uss',
        author_email = 'unclerus@gmail.com',
        url = 'https://github.com/UncleRus/cherryBase',
        license = 'BSD',
        scripts = ['bin/cherrybased'],
        packages = [
            'cherrybase',
            'cherrybase.db',
            'cherrybase.db.drivers',
            'cherrybase.tools',
            'cherrybase.orm',
            'cherrybase.orm.drivers',
            'cherrybase.forms',
        ],
        data_files = [
            ('bin', ['bin/cherrybased'])
        ],
        install_requires = ['CherryPy >= 3.2', 'python-gnupg >= 0.3.5']
    )


if __name__ == "__main__":
    main ()
