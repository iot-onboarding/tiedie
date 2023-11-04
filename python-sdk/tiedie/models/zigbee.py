#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0
"""

Python module for Zigbee communication, including classes for attributes, 
clusters, endpoints, and various Zigbee request types.

"""

from typing import Union
from .common import *


class Attribute:
    """ Stores attribute information with an ID and type. """
    attribute_id: int
    attribute_type: int


class Cluster:
    """ Represents clusters with an ID and a list of attributes. """
    cluster_id: int
    attributes: list[Attribute]


class Endpoint:
    """ Represents endpoints with an ID and a list of clusters. """
    endpoint_id: int
    clusters: list[Cluster]


class ZigbeeReadRequest:
    """ Request to read Zigbee data from specific attributes. """
    endpoint_id: Union[None, int] = None
    cluster_id: Union[None, int] = None
    attribute_id: Union[None, int] = None
    type_: Union[None, int] = None


class ZigbeeWriteRequest:
    """ Request to write data to Zigbee attributes. """
    def __init__(self, endpoint_id, cluster_id, attribute_id, type_, data):
        self.endpoint_id = endpoint_id
        self.cluster_id = cluster_id
        self.attribute_id = attribute_id
        self.type = type_
        self.data = data


class ZigbeeSubscribeRequest: 
    """ Request to subscribe to Zigbee attribute changes. """
    def __init__(self, endpointID: int, clusterID: int, attributeID: int,
                 type: int, minReportTime: int, maxReportTime: int):
        self.endpointID = endpointID
        self.clusterID = clusterID
        self.attributeID = attributeID
        self.type = type
        self.minReportTime = minReportTime
        self.maxReportTime = maxReportTime


class ZigbeeDataParameter(DataParameter):
    """  Zigbee data with device and attribute information. """
    def __init__(self, device_id: str, endpoint_id: int, cluster_id: int,
                 attribute_id: int, type_: int = None):
        super().__init__(device_id)
        self.endpoint_id = endpoint_id
        self.cluster_id = cluster_id
        self.attribute_id = attribute_id
        self.type = type_


class ZigbeeDiscoverResponse:
    """ Response containing discovered Zigbee endpoint data. """
    def __init__(self):
        self.endpoints = [Endpoint]


    def to_parameter_list(self, device_id: str):
        """ Function to return parameter list """
        parameters = []

        for endpoint in self.endpoints:
            for cluster in endpoint.clusters:
                for attribute in cluster.attributes:
                    parameter = ZigbeeDataParameter(device_id, endpoint.endpoint_id, cluster.cluster_id, attribute.attribute_id, attribute.attribute_type)
                    parameters.append(parameter)

        return parameters


class ZigbeeUnsubscribeRequest:
    """ Request to unsubscribe from Zigbee attribute changes. """
    def __init__(self, endpointID: int, clusterID: int, attributeID: int, type: int):
        self.endpointID = endpointID
        self.clusterID = clusterID
        self.attributeID = attributeID
        self.type = type


class ZigbeeRegisterTopicRequest:
    """ Request to unsubscribe from Zigbee attribute changes. """
    endpointID: int
    clusterID: int
    attributeID: int
    type: int
