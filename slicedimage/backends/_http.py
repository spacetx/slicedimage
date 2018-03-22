from __future__ import absolute_import, division, print_function, unicode_literals

import requests
from six.moves import urllib

from ._base import Backend


class HttpBackend(Backend):
    def __init__(self, baseurl):
        self._baseurl = baseurl

    def read_file_handle_callable(self, name, checksum_sha1):
        def returned_callable():
            parsed = urllib.parse.urljoin(self._baseurl, name)
            req = requests.get(parsed, stream=True)
            return req.raw
        return returned_callable
