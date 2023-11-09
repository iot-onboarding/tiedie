#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
"""

This moddules defines a client for making HTTP requests, handling responses, 
and mapping them to specific classes, particularly for IoT applications.

"""

from enum import Enum
import json
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
import requests
from tiedie.api.auth import Authenticator
from tiedie.models.responses import (
    HttpResponse,
    TiedieHTTP,
    TiedieRawResponse,
    TiedieResponse,
    TiedieStatus
)


ReturnClass = TypeVar('ReturnClass', bound=BaseModel)
TiedieReturnClass = TypeVar('TiedieReturnClass', bound=TiedieRawResponse)


class AbstractHttpClient:
    """ class AbstractHttpClient """

    def __init__(self, base_url, media_type, authenticator: Authenticator):
        self.base_url = base_url
        self.media_type = media_type
        self.headers = {"Content-Type": self.media_type}
        self.http_client = authenticator.set_auth_options(requests.Session())

    def _map_response(self,
                      response: requests.Response,
                      return_class: Optional[Type[ReturnClass]] = None) \
            -> HttpResponse[ReturnClass | None]:
        """ Map response to object """
        if return_class is None:
            return HttpResponse[ReturnClass | None](
                response.status_code,
                response.reason,
                None
            )

        body = return_class.model_validate_json(
            response.text)

        return HttpResponse[ReturnClass | None](
            response.status_code,
            response.reason,
            body
        )

    def post(self,
             path: str,
             body: BaseModel,
             return_class: Optional[Type[ReturnClass]] = None) -> HttpResponse[ReturnClass | None]:
        """ API POST """
        response = self.http_client.post(
            self.base_url + path,
            data=body.model_dump_json(by_alias=True, exclude_none=True),
            headers=self.headers,
            verify=False,
        )

        return self._map_response(response, return_class)

    def get(self,
            path: str,
            return_class: Optional[Type[ReturnClass]] = None) -> HttpResponse[ReturnClass | None]:
        """ API GET """

        response = self.http_client.get(
            self.base_url + path,
            headers=self.headers,
            verify=False,

        )
        return self._map_response(response, return_class)

    def delete(self,
               path: str,
               return_class: Optional[Type[ReturnClass]] = None) \
            -> HttpResponse[ReturnClass | None]:
        """ API DELETE """
        response = self.http_client.delete(
            self.base_url + path,
            headers=self.headers,
            verify=False,
        )

        return self._map_response(response, return_class)

    def _map_tiedie_response(self,
                             response: requests.Response,
                             return_class: Optional[Type[TiedieReturnClass]] = None) \
            -> TiedieRawResponse:
        """ Map response to object """
        http = TiedieHTTP(
            status_code=response.status_code,
            status_message=response.reason
        )

        if return_class is None:
            tiedie_response = TiedieResponse[None].model_validate_json(
                response.text)
            tiedie_response.http = http
            return tiedie_response

        try:
            tiedie_response = return_class.model_validate_json(response.text)
            tiedie_response.http = http
        except (ValueError, ValidationError):
            tiedie_response = TiedieResponse[None](
                status=TiedieStatus.FAILURE,
                http=http
            )

        return tiedie_response

    def _get_query_parameters(self, body: BaseModel):
        if body is None:
            return []

        object_map = body.model_dump(by_alias=True, exclude_none=True)
        query_parameters = []

        stack = list(object_map.items())

        while stack:
            key, value = stack.pop()
            if isinstance(value, Enum):
                value = value.value
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    stack.append((key + "[" + sub_key + "]", sub_value))
            elif isinstance(value, list):
                for sub_value in value:
                    stack.append((key, sub_value))
            elif isinstance(value, bool):
                query_parameters.append((key, json.dumps(value)))
            else:
                query_parameters.append((key, str(value)))

        query_parameters.reverse()

        return query_parameters

    def post_with_tiedie_response(self,
                                  path: str,
                                  body: BaseModel,
                                  return_class: Optional[Type[TiedieReturnClass]] = None) -> \
            TiedieRawResponse:
        """ API POST with tiedie response """

        response = self.http_client.post(
            self.base_url + path,
            data=body.model_dump_json(by_alias=True, exclude_none=True),
            headers=self.headers,
            verify=False,
        )

        return self._map_tiedie_response(response, return_class)

    def get_with_tiedie_response(self,
                                 path: str,
                                 body: BaseModel,
                                 return_class: Optional[Type[TiedieReturnClass]] = None) -> \
            TiedieRawResponse:
        """ API GET with tiedie response """

        response = self.http_client.get(
            self.base_url + path,
            headers=self.headers,
            params=self._get_query_parameters(body),
            verify=False,
        )

        return self._map_tiedie_response(response, return_class)

    def delete_with_tiedie_response(self,
                                    path: str,
                                    body: BaseModel,
                                    return_class: Optional[Type[TiedieReturnClass]] = None) -> \
            TiedieRawResponse:
        """ API DELETE with tiedie response """

        response = self.http_client.delete(
            self.base_url + path,
            params=self._get_query_parameters(body),
            headers=self.headers,
            verify=False,
        )

        return self._map_tiedie_response(response, return_class)
