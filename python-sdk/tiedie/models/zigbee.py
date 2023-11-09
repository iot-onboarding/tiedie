#!python
# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

Python module for Zigbee communication, including classes for attributes, 
clusters, endpoints, and various Zigbee request types.

"""


from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from tiedie.models.common import DataParameter
from tiedie.models.responses import TiedieRawResponse


class Attribute(BaseModel):
    """ Stores attribute information with an ID and type. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    attribute_id: int
    attribute_type: int


class Cluster(BaseModel):
    """ Represents clusters with an ID and a list of attributes. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    cluster_id: int
    attributes: list[Attribute]


class Endpoint(BaseModel):
    """ Represents endpoints with an ID and a list of clusters. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    endpoint_id: int
    clusters: list[Cluster]


class ZigbeeReadRequest(BaseModel):
    """ Request to read Zigbee data from specific attributes. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    endpoint_id: Optional[int] = None
    cluster_id: Optional[int] = None
    attribute_id: Optional[int] = None
    type_: Optional[int] = None


class ZigbeeWriteRequest(BaseModel):
    """ Request to write data to Zigbee attributes. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    endpoint_id: int
    cluster_id: int
    attribute_id: int
    type: int


class ZigbeeDataParameter(DataParameter):
    """  Zigbee data with device and attribute information. """

    endpoint_id: str
    cluster_id: int
    attribute_id: int
    attribute_type: int


class ZigbeeDiscoverResponse(TiedieRawResponse):
    """ Response containing discovered Zigbee endpoint data. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    endpoints: List[Endpoint]

    def to_parameter_list(self, device_id: str):
        """ Function to return parameter list """
        parameters = []

        for endpoint in self.endpoints:
            for cluster in endpoint.clusters:
                for attribute in cluster.attributes:
                    parameter = ZigbeeDataParameter(
                        device_id=device_id,
                        endpoint_id=endpoint.endpoint_id,
                        cluster_id=cluster.cluster_id,
                        attribute_id=attribute.attribute_id,
                        attribute_type=attribute.attribute_type)
                    parameters.append(parameter)

        return parameters


class ZigbeeRegisterTopicRequest(BaseModel):
    """ Request to unsubscribe from Zigbee attribute changes. """

    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    endpoint_id: int = Field(alias="endpointID")
    cluster_id: int = Field(alias="clusterID")
    attribute_id: int = Field(alias="attributeID")
    attribute_type: int
