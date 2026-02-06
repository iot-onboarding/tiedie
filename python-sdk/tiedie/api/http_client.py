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
import logging
from typing import Optional, Type, TypeVar, Union, List
from pydantic import BaseModel, ValidationError
import requests
from tiedie.api.auth import Authenticator
from tiedie.models.responses import (
    HttpResponse,
    TiedieHTTP,
    NipcResponse,
    ProblemDetails
)


ReturnClass = TypeVar('ReturnClass', bound=BaseModel)
NipcReturnClass = TypeVar('NipcReturnClass', bound=BaseModel)

logger = logging.getLogger('tiedie')

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

        logger.debug("Response HTTP status %d", response.status_code)
        logger.debug("Response headers: %s", response.headers)
        logger.debug("Response: %s", response.text)

        try:
            body = return_class.model_validate_json(
                response.text)
        except (ValueError, ValidationError):
            body = None

        return HttpResponse[ReturnClass | None](
            response.status_code,
            response.reason,
            body
        )

    def post(self,
             path: str,
             body: BaseModel,
             return_class: Type[ReturnClass]) -> HttpResponse[ReturnClass | None]:
        """ API POST """
        data = body.model_dump_json(by_alias=True, exclude_none=True)

        logger.debug("POST %s", self.base_url + path)
        logger.debug("Headers: %s", self.headers)
        logger.debug("Body: %s", data)

        response = self.http_client.post(
            self.base_url + path,
            data=data,
            headers=self.headers,
            verify=False,
        )

        return self._map_response(response, return_class)

    def put(self,
             path: str,
             body: BaseModel,
             return_class: Type[ReturnClass]) -> HttpResponse[ReturnClass | None]:
        """ API PUT """
        data = body.model_dump_json(by_alias=True, exclude_none=True)

        logger.debug("PUT %s", self.base_url + path)
        logger.debug("Headers: %s", self.headers)
        logger.debug("Body: %s", data)

        response = self.http_client.put(
            self.base_url + path,
            data=data,
            headers=self.headers,
            verify=False,
        )

        return self._map_response(response, return_class)

    def get(self,
            path: str,
            return_class: Type[ReturnClass]) -> HttpResponse[ReturnClass | None]:
        """ API GET """

        logger.debug("GET %s", self.base_url + path)
        logger.debug("Headers: %s", self.headers)

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

        logger.debug("DELETE %s", self.base_url + path)
        logger.debug("Headers: %s", self.headers)

        response = self.http_client.delete(
            self.base_url + path,
            headers=self.headers,
            verify=False,
        )

        return self._map_response(response, return_class)

    def _map_nipc_response(self,
                          response: requests.Response,
                          return_class: Optional[Type[NipcReturnClass]]) \
            -> NipcResponse[Optional[NipcReturnClass]]:
        """Map HTTP response to NIPC response format.

        Handles both success responses (HTTP 200 with JSON) and error responses
        (HTTP 4xx/5xx with Problem Details format).
        """
        http = TiedieHTTP(
            status_code=response.status_code,
            status_message=response.reason,
            headers=dict(response.headers)
        )

        logger.debug("Response headers: %s", response.headers)
        logger.debug("Response: %s", response.text)

        # Check for error status codes (4xx, 5xx)
        if response.status_code >= 400:
            return self._handle_error_response(response, http)

        # Handle success response (2xx)
        return self._handle_success_response(response, http, return_class)

    def _handle_error_response(self,
                              response: requests.Response,
                              http: TiedieHTTP) -> NipcResponse[None]:
        """Handle error responses with Problem Details format."""
        content_type = response.headers.get('content-type', '').lower()

        try:
            if 'application/problem+json' in content_type:
                # Parse RFC 9457 Problem Details format
                problem_details = ProblemDetails.model_validate_json(response.text)
                return NipcResponse[None](http=http, error=problem_details)
            # Fallback: try to parse as JSON and extract error info
            error_data = json.loads(response.text) if response.text else {}
            problem_details = ProblemDetails(
                type="about:blank",  # RFC 9457 default for generic errors
                status=response.status_code,
                title=response.reason or "HTTP Error",
                detail=error_data.get('detail') or error_data.get('message') or response.text
            )
            return NipcResponse[None](http=http, error=problem_details)
        except (ValueError, ValidationError, json.JSONDecodeError) as e:
            logger.debug("Error parsing error response: %s", e)
            # Create generic problem details for unparseable errors
            problem_details = ProblemDetails(
                type="about:blank",
                status=response.status_code,
                title=response.reason or "HTTP Error",
                detail=f"Failed to parse error response: {str(e)}"
            )
            return NipcResponse[None](http=http, error=problem_details)

    def _handle_success_response(self,
                                response: requests.Response,
                                http: TiedieHTTP,
                                return_class: Optional[Type[NipcReturnClass]]) \
        -> NipcResponse[Optional[NipcReturnClass]]:
        """Handle successful responses."""
        if return_class is None:
            return NipcResponse[None](http=http, body=None)
        try:
            body = return_class.model_validate_json(response.text)
            return NipcResponse[Optional[NipcReturnClass]](http=http, body=body)
        except (ValueError, ValidationError) as e:
            logger.debug("Error parsing success response: %s", e)
            # If parsing fails, treat as error
            problem_details = ProblemDetails(
                type="about:blank",
                status=500,  # Internal server error for parsing issues
                title="Response Parsing Error",
                detail=f"Failed to parse response as {return_class.__name__}: {str(e)}"
            )
            return NipcResponse[None](http=http, error=problem_details)

    def _get_query_parameters(self, body: Optional[BaseModel]):
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
                query_parameters.append((key, ",".join(value)))
            elif isinstance(value, bool):
                query_parameters.append((key, json.dumps(value)))
            else:
                query_parameters.append((key, str(value)))

        query_parameters.reverse()

        return query_parameters

    def _serialize_body(self, body: Optional[Union[BaseModel, List[BaseModel]]]) -> Optional[str]:
        """Serialize body parameter to JSON string.

        Args:
            body: Either a single BaseModel, a list of BaseModel instances, or None

        Returns:
            JSON string representation of the body, or None if body is None
        """
        if body is None:
            return None

        if isinstance(body, list):
            # Handle list of BaseModel instances
            return '[' + \
                ','.join([
                    item.model_dump_json(
                        by_alias=True,
                        exclude_none=True
                    ) for item in body
                ]) + \
                ']'
        return body.model_dump_json(by_alias=True, exclude_none=True)

    def post_with_nipc_response(self,
                           path: str,
                           body: Optional[Union[BaseModel, List[BaseModel]]],
                           return_class: Optional[Type[NipcReturnClass]],
                           content_type: Optional[str] = "application/nipc+json") -> \
        NipcResponse[Optional[NipcReturnClass]]:
        """ API POST with NIPC response format """

        data = self._serialize_body(body)

        self.headers['Content-Type'] = content_type

        logger.debug("POST %s", self.base_url + path)
        logger.debug("Headers: %s", self.headers)
        logger.debug("Body: %s", data)

        response = self.http_client.post(
            self.base_url + path,
            data=data,
            headers=self.headers,
            verify=False,
        )

        return self._map_nipc_response(response, return_class)


    def put_with_nipc_response(self,
                              path: str,
                              body: Union[BaseModel, List[BaseModel]],
                              return_class: Optional[Type[NipcReturnClass]],
                              content_type: Optional[str] = "application/nipc+json") -> \
            NipcResponse[Optional[NipcReturnClass]]:
        """ API PUT with NIPC response format """

        data = self._serialize_body(body)

        self.headers['Content-Type'] = content_type

        logger.debug("PUT %s", self.base_url + path)
        logger.debug("Headers: %s", self.headers)
        logger.debug("Body: %s", data)

        response = self.http_client.put(
            self.base_url + path,
            data=data,
            headers=self.headers,
            verify=False,
        )

        return self._map_nipc_response(response, return_class)



    def get_with_nipc_response(self,
                              path: str,
                              body: Optional[BaseModel],
                              return_class: Optional[Type[NipcReturnClass]]) -> \
            NipcResponse[Optional[NipcReturnClass]]:
        """ API GET with NIPC response format """

        params = self._get_query_parameters(body)

        logger.debug("GET %s", self.base_url + path)
        logger.debug("Headers: %s", self.headers)
        logger.debug("Params: %s", params)

        response = self.http_client.get(
            self.base_url + path,
            headers=self.headers,
            params=params,
            verify=False,
        )

        return self._map_nipc_response(response, return_class)


    def delete_with_nipc_response(self,
                                 path: str,
                                 body: Optional[BaseModel],
                                 return_class: Optional[Type[NipcReturnClass]]) -> \
            NipcResponse[Optional[NipcReturnClass]]:
        """ API DELETE with NIPC response format """

        params = self._get_query_parameters(body)

        logger.debug("DELETE %s", self.base_url + path)
        logger.debug("Headers: %s", self.headers)
        logger.debug("Params: %s", params)

        response = self.http_client.delete(
            self.base_url + path,
            params=params,
            headers=self.headers,
            verify=False,
        )

        return self._map_nipc_response(response, return_class)
