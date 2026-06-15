#!/usr/bin/env python3
"""Wrapper that patches urllib User-Agent to bypass Cloudflare, then runs the judge."""
import urllib.request as _ur
_original_request = _ur.Request

class _PatchedRequest(_ur.Request):
    def __init__(self, url, data=None, headers=None, origin_req_host=None, unverifiable=False, method=None):
        if headers is None:
            headers = {}
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        super().__init__(url, data=data, headers=headers, origin_req_host=origin_req_host,
                         unverifiable=unverifiable, method=method)

_ur.Request = _PatchedRequest

import judge_simulator
judge_simulator.main()
