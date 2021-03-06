# Copyright (c) 2013 The Johns Hopkins University/Applied Physics Laboratory
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Test cases for the conf key manager.
"""

import binascii

from castellan.common.objects import symmetric_key as key
from oslo_config import cfg

from cinder import context
from cinder import exception
from cinder.keymgr import conf_key_mgr
from cinder.tests.unit import test

CONF = cfg.CONF
CONF.import_opt('fixed_key', 'cinder.keymgr.conf_key_mgr', group='key_manager')


class ConfKeyManagerTestCase(test.TestCase):
    def __init__(self, *args, **kwargs):
        super(ConfKeyManagerTestCase, self).__init__(*args, **kwargs)

        self._hex_key = '1' * 64

    def _create_key_manager(self):
        CONF.set_default('fixed_key', default=self._hex_key,
                         group='key_manager')
        return conf_key_mgr.ConfKeyManager(CONF)

    def setUp(self):
        super(ConfKeyManagerTestCase, self).setUp()
        self.key_mgr = self._create_key_manager()

        self.ctxt = context.RequestContext('fake', 'fake')

        self.key_id = '00000000-0000-0000-0000-000000000000'
        encoded = bytes(binascii.unhexlify(self._hex_key))
        self.key = key.SymmetricKey('AES', len(encoded) * 8, encoded)

    def test___init__(self):
        self.assertEqual(self.key_id, self.key_mgr.key_id)

    def test_create_key(self):
        key_id_1 = self.key_mgr.create_key(self.ctxt)
        key_id_2 = self.key_mgr.create_key(self.ctxt)
        # ensure that the UUIDs are the same
        self.assertEqual(key_id_1, key_id_2)

    def test_create_null_context(self):
        self.assertRaises(exception.NotAuthorized,
                          self.key_mgr.create_key, None)

    def test_create_key_pair(self):
        self.assertRaises(NotImplementedError,
                          self.key_mgr.create_key_pair, self.ctxt)

    def test_create_key_pair_null_context(self):
        self.assertRaises(NotImplementedError,
                          self.key_mgr.create_key_pair, None)

    def test_store_key(self):
        key_id = self.key_mgr.store(self.ctxt, self.key)

        actual_key = self.key_mgr.get(self.ctxt, key_id)
        self.assertEqual(self.key, actual_key)

    def test_store_null_context(self):
        self.assertRaises(exception.NotAuthorized,
                          self.key_mgr.store, None, self.key)

    def test_store_key_invalid(self):
        encoded = bytes(binascii.unhexlify('0' * 64))
        inverse_key = key.SymmetricKey('AES', len(encoded) * 8, encoded)

        self.assertRaises(exception.KeyManagerError,
                          self.key_mgr.store, self.ctxt, inverse_key)

    def test_delete_key(self):
        key_id = self.key_mgr.create_key(self.ctxt)
        self.key_mgr.delete(self.ctxt, key_id)

        # cannot delete key -- might have lingering references
        self.assertEqual(self.key,
                         self.key_mgr.get(self.ctxt, self.key_id))

    def test_delete_null_context(self):
        self.assertRaises(exception.NotAuthorized,
                          self.key_mgr.delete, None, None)

    def test_delete_unknown_key(self):
        self.assertRaises(exception.KeyManagerError,
                          self.key_mgr.delete, self.ctxt, None)

    def test_get_key(self):
        self.assertEqual(self.key,
                         self.key_mgr.get(self.ctxt, self.key_id))

    def test_get_null_context(self):
        self.assertRaises(exception.NotAuthorized,
                          self.key_mgr.get, None, None)

    def test_get_unknown_key(self):
        self.assertRaises(KeyError, self.key_mgr.get, self.ctxt, None)

    def test_list(self):
        keys = self.key_mgr.list(self.ctxt)
        self.assertEqual(0, len(keys))

    def test_list_null_context(self):
        self.assertRaises(exception.NotAuthorized,
                          self.key_mgr.list, None)
