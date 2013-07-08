# -*- coding: utf-8 -*-

import sqlalchemy.schema as sas
import sqlalchemy.types as sat
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base ()

class Rights (Base):

    __tablename__ = 'rights'

    fingerprint = sas.Column (sat.String (50), primary_key = True, nullable = False)
    method = sas.Column (sat.Text, primary_key = True, nullable = False)

    def __init__ (self, fingerprint, method):
        self.fingerprint = fingerprint
        self.method = method
