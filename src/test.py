#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xmlrpclib
from rco import gpgxmlrpc

server = xmlrpclib.Server (
    'http://rpc.cherrybase:8080/',
    allow_none = True,
    transport = gpgxmlrpc.GpgTransport (
        gpg_homedir = '/home/rus/work/home/cherryBase/src/rpciface/keyring',
        gpg_key = '55A6F35DC05A3728FB45AA0277EA551D7EAC9ABD',
        gpg_password = '123321',
        gpg_server_key = '55A6F35DC05A3728FB45AA0277EA551D7EAC9ABD',
    )
)

print server.system.listMethods ()
print server.test.hello (u'Миииир!')

keys = server.control.keyring.keys ()
print keys

print server.control.keyring.export (keys.keys ())

print server.control.keyring.append ('''
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.12 (GNU/Linux)

mQGiBDXaayARBADDLdW4aij9O8HqLS/WxTYbGKUF6skz0NANFq7SSrAyF4cOj6OQ
AMo1KqrI+1KpZa7Os/AaZXrlu6vcsmVjCR/x15g0XePRDseMYw0dMqu5fE0VEbmx
UuHTOk9ocTYPr8cdT5h7aDpdTVtfQOgIngeNHtOkVohggvt3MiS0PUWwJQCg/ytm
CzTxPuockcXQi12w5R+wLGcEAKpsAEhQQT0Lm7N/LWETGbIFAYg5yPqIpm7JQV9u
7IOk/i8uzeXp2y27WTOYwrnlmdLL3eSTThd308CUxyPg46eGITv2jb1jDb2/bp9D
c1+mESXOYcyvj9havINwhx+OsEp64PlhmBlVtFGvS1XddiLhJv4VaYYqZlELqwo5
FmyYA/9dq7/vf2AJH+w4nD4k0j0lZdxXIFYoJ9IGX0XkOKSiANjJV0cxSX/Gtcg6
uf1KLme0y+rY4NcbU6fHm+SE7/qZ2jbhbyKJG8w15JLvKMEAJSCLdarl58f+7fKg
Ih8tQcNVCtf0F6isqvweLfzCFDNwOAHZqQIDoIFDjEPttmTNv7QcTGFycnkgU3Vz
YW5rYSA8bHNAYmxhcmcubmV0PohLBBARAgALBQI12msgBAsDAQIACgkQnnQBohDC
8ySGqgCeL3njNNn43EKwabeC25wbYCUE/doAn2C3nopFhLJhIVSpp9t1Sjh0Yc8m
tCRMYXJyeSBTdXNhbmthIDxsc3VzYW5rYUBjdGMuY3RjLmVkdT6ISwQQEQIACwUC
NeJCTAQLAwECAAoJEJ50AaIQwvMkdhIAn2+XGEGYUBCghHA/Sa/1iazHP9/cAJ4m
UxSrX4nuGSXN/8hlxubzTeEbdrQkTGFycnkgU3VzYW5rYSA8bHNAcHJpbWUuYmNj
LmN0Yy5lZHU+iEsEEBECAAsFAjXiQdAECwMBAgAKCRCedAGiEMLzJLLjAJ9ZzVUX
U5JJsd0+23Xo2NbPiPmDtACgpYL3678TsGfecsgsSYdtbRG1v8y0JExhcnJ5IFN1
c2Fua2EgPGxzdXNhbmthQGJjYy5jdGMuZWR1PohLBBARAgALBQI14kKMBAsDAQIA
CgkQnnQBohDC8yRQ/QCggoPpgT/wRxUO1uzODLO+aiMkZkcAoKy7JCo15U2E1Hom
zkShmknjOxpouQMNBDXadu4QDADB1xK+tTpX4OmSvP5CyEvYh+Ipr4asOfkxCEgq
DfJq92nWQZAB1SwhLkebybJXurHNTpq/TGpXU6neetJ03lzdxmRTtHCUDtV1nGtk
xFrRJfWvJsRUQ/LehkkJcbsW9GE67q7uOmSMkjjW21AeDJrABiioCqe+3SJVFb5w
zE2OsIuI9TVmB+Ru+KpLc47GhENZNzhiQ7ZHtVzs8GwYWfBUwcu7ibeEuVTKbzch
Bq6uFDozFSEbe1a0WyAYA6ahjBHMoItYEap5RDUDWMjOEnEI9253ujRrqLhlHrjj
4oFU+xp3dtHs7oxsE8Bt3eP1dzDT8G5+9lApzI9FGTbFn581ALo+qPiDYF/XdgoT
evvXv6C8bI16DcHGcwHqM6zWQHYf+4wVa5f7dEMNYUQIiIJaHXH8f6qFNFH1bOL/
ENXUXsHEdU4+WdqqVxYE8PSgMsOCIZQfVWgM8xuQe+PqCtw9nlMVO3CN+KaW6+dj
H+LhBSXCd+odgvzB4D7W6R+Hvf8AAgIL/0wv9/f6aM8ZUpH/J9lkuUWqI36/7NPD
tqMLmh5DSry7kHvKg38JcofZUnEMeDx+O0PClax4vvl+gKoi+2O5/cxJYExGxqST
sIuqYCbldicVV5p+st14sYmEqwpm7i6Wq4FbzOeg1orWDCJvfCB8KfEn7RCLo+o4
qXufC+YtH/TuTd/vuyb7/lZx8KoXCS+S0Yd5DIcbX5w5um1tM9+QulXown7r4B2m
hKur/Vov8lnIIBgvU8VAUJ5+CC5YZZaH0vIZvva5Beu7UuBvwwxzzw3kbMuGLrtc
i+x21CCi6Kba8nB4GWgQnksdDKuNFw16qClGQxZmO8HAvZKKiZMGaczIEJSTMXGS
jPdFy+0VSu3SnySk2m6iJK5E/2pKFaIhqcI/QfW+6OH2nFLbtpMVHywNSf3W2C8d
Sca149hqsRlwFIIfIbnVv2OnQlTNyTI543bv1Vz+evTf1+KQ4ExSUe6HQg4yQwgO
C6pldyY4/SNscN1B7EX9EGeCwnihL6/wmog/AwUYNdp27p50AaIQwvMkEQL3AACf
TBdOMVeCVFrk1MI0zywr24EcrSwAoIks+DJ1tx8eC03WgYT9IQOT6UrO
=NvTy
-----END PGP PUBLIC KEY BLOCK-----

''')

print server.control.keyring.keys ()

#server.control.keyring.remove ('0B5C0DEF06026FD84870ABDB9E7401A210C2F324')

print server.control.keyring.keys ()
