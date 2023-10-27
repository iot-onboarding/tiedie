#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

import json
import requests
from enum import Enum


class TiedieStatus(Enum):
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"


class TiedieResponse:
    def __init__(self, status, httpStatusCode, httpMessage, body, map: dict = None):
        self.status = status
        self.httpStatusCode = httpStatusCode
        self.httpMessage = httpMessage
        self.body = body
        self.map = map


    def unpack_remaining(self, key, value):
        self.map[key] = value


    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
        
class HttpResponse:
    def __init__(self, status_code, message, body):
        self.status_code = status_code
        self.message = message
        self.body = body


class AbstractHttpClient:
    def __init__(self, base_url, media_type, authenticator):
        self.base_url = base_url
        self.media_type = media_type
        self.http_client = authenticator.set_auth_options(requests.Session())

    
    def map_response(self, response, return_class):
        http_response = HttpResponse(
            response.status_code,
            response.reason,
            None
        )
        
        try:
            http_response.body = json.loads(response.content.decode("utf-8"))
        except ValueError:
            pass

        return http_response
    

    def post(self, path, body, return_class):
        headers = {
            "Content-Type": self.media_type
        }

        response = self.http_client.post(
            self.base_url + path,
            data=json.dumps(body, default=lambda o: o.__json__()),
            headers=headers,
            verify=False,
        )

        return self.map_response(response, return_class)
    

    def get(self, path, return_class, params=None):
        headers = {"Content-Type": self.media_type}

        response = self.http_client.get(
            self.base_url + path,
            headers=headers,
            verify=False,
            params=params
            
        )

        return self.map_response(response, return_class)
    

    def delete(self, path, return_class, params=None):
        headers = {
            "Content-Type": self.media_type
        }

        response = self.http_client.delete(
            self.base_url + path,
            headers=headers,
            verify=False,
            params=params
        )

        return self.map_response(response, return_class)
    

    def post_with_tiedie_response(self, path, body, return_class):
        
        headers = {"Content-Type": self.media_type}

        response = self.http_client.post(
            self.base_url + path,
            data=json.dumps(body, default=lambda o: o.__json__()),
            headers=headers,
            verify=False,
        )

        tiedie_response = TiedieResponse(
            TiedieStatus.FAILURE,
            response.status_code,
            response.reason,
            None
        )

        try:
            json_data = json.loads(response.text)

            tiedie_response.http_status_code = response.status_code
            tiedie_response.http_message = response.reason

            tiedie_response.map = json_data
            constructor_args = {k: v for k, v in json_data.items() if k in return_class.__init__.__code__.co_varnames}
            tiedie_response.body = return_class(**constructor_args)

        except json.JSONDecodeError or ValueError:
            pass

        except KeyError:
            tiedie_response = TiedieResponse(
                TiedieStatus.FAILURE,
                response.status_code,
                response.reason,
                None
            )
            
        return tiedie_response
