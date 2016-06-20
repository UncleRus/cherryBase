#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__version__ = '0.4.7'

def main ():
    setup (
        name = 'cherrybase',
        version = __version__,
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
        license = 'LGPLv3',
        scripts = ['scripts/cherrybased'],
        packages = [
            'cherrybase',
            'cherrybase.db',
            'cherrybase.db.drivers',
            'cherrybase.tools',
            'cherrybase.tools.auth',
            'cherrybase.orm',
            'cherrybase.orm.drivers',
        ],
        #data_files = [
        #    ('bin', ['bin/cherrybased'])
        #],
        install_requires = ['cherrypy >= 3.2']
    )


if __name__ == "__main__":
    main ()
