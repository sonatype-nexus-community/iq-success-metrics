""" test_audit.py , for all your testing of audit py needs """
# Copyright 2019 Sonatype Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest

from success_metrics import searchApps


class TestSuccessMetrics(unittest.TestCase):
    """ TestSuccessMetrics is responsible for testing success_metrics.py """

    def test_search_apps_search_empty(self):
        """ ensures when called with an empty search value, the expected empty result is returned """
        self.assertEqual([], searchApps("", "iqurl-value"))
