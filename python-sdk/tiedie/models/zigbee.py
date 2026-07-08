#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
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
from tiedie.models.responses import SuccessResponse


class Attribute(BaseModel):
    """ Stores attribute information with an ID and type. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    attribute_id: int = Field(alias=str("attributeID"))
    attribute_type: int


class Cluster(BaseModel):
    """ Represents clusters with an ID and a list of attributes. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    cluster_id: int = Field(alias=str("clusterID"))
    attributes: Optional[list[Attribute]] = None


class Endpoint(BaseModel):
    """ Represents endpoints with an ID and a list of clusters. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    endpoint_id: int = Field(alias=str("endpointID"))
    clusters: Optional[list[Cluster]] = None


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

    endpoint_id: int
    cluster_id: int
    attribute_id: int
    attribute_type: int


class ZigbeeDiscoverEndpoints(BaseModel):
    """ Represents a collection of Zigbee endpoints. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    endpoints: Optional[List[Endpoint]] = None


class ZigbeeDiscoverProtocolInformation(BaseModel):
    """ Represents protocol information for Zigbee. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    zigbee: ZigbeeDiscoverEndpoints


class ZigbeeDiscoverResponse(SuccessResponse):
    """ Response containing discovered Zigbee endpoint data. """
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    device_id: str = Field(alias=str("id"))
    protocol_information: Optional[ZigbeeDiscoverProtocolInformation] = None

    def to_parameter_list(self, device_id: str) -> List[ZigbeeDataParameter]:
        """ Function to return parameter list """
        parameters: List[ZigbeeDataParameter] = []

        if self.protocol_information is None:
            return parameters

        for endpoint in self.protocol_information.zigbee.endpoints or []:
            for cluster in endpoint.clusters or []:
                for attribute in cluster.attributes or []:
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
