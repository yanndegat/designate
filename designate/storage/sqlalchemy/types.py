# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import re
import uuid

from sqlalchemy.types import TypeDecorator, CHAR, String
from sqlalchemy.dialects.postgresql import UUID as pgUUID

import designate.conf
from designate.storage.sqlalchemy import tables


CONF = designate.conf.CONF


class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    Copied verbatim from SQLAlchemy documentation.
    """
    cache_ok = True
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(pgUUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return str(uuid.UUID(value))


class DNSRecordTypes(TypeDecorator):
    """
    A custom string type that validates whether the value is:
    1. A string within a list of DNS record types allowed values, or
    2. A string that matches with "^TYPE[0-9]*".
    """
    cache_ok = True
    impl = String(10)

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif value in tables.RECORD_TYPES or (
                CONF.support_generic_record_types and
                re.match(r'^TYPE\d+$', value)
                if isinstance(value, str) else False):
            return value
        else:
            err_msg = ("Value '%(value)s' in table is not valid."
                       " Must be in [%(record_types)s] or match "
                       "'^TYPE\\d$'"
             % {'value': value,
                'record_types': ', '.join(tables.RECORD_TYPES)})
            raise ValueError(err_msg)
        return value
