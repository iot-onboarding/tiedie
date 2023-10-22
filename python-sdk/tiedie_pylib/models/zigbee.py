#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See accompanying LICENSE file in this distribution.

from .common import *
from typing import Union


class Attribute:
    attribute_id: int
    attribute_type: int


class Cluster:
    cluster_id: int
    attributes: list[Attribute]


class Endpoint:
    endpoint_id: int
    clusters: list[Cluster]


class ZigbeeReadRequest:
    endpoint_id: Union[None, int] = None
    cluster_id: Union[None, int] = None
    attribute_id: Union[None, int] = None
    type_: Union[None, int] = None


class ZigbeeWriteRequest:
    def __init__(self, endpoint_id, cluster_id, attribute_id, type_, data):
        self.endpoint_id = endpoint_id
        self.cluster_id = cluster_id
        self.attribute_id = attribute_id
        self.type = type_
        self.data = data


class ZigbeeSubscribeRequest:
    def __init__(self, endpointID: int, clusterID: int, attributeID: int, type: int, minReportTime: int, maxReportTime: int):
        self.endpointID = endpointID
        self.clusterID = clusterID
        self.attributeID = attributeID
        self.type = type
        self.minReportTime = minReportTime
        self.maxReportTime = maxReportTime


class ZigbeeDataParameter(DataParameter):
    def __init__(self, device_id: str, endpoint_id: int, cluster_id: int, attribute_id: int, type_: int = None):
        super().__init__(device_id)
        self.endpoint_id = endpoint_id
        self.cluster_id = cluster_id
        self.attribute_id = attribute_id
        self.type = type_


class ZigbeeDiscoverResponse:
    def __init__(self):
        self.endpoints = [Endpoint]


    def to_parameter_list(self, device_id: str):
        parameters = []

        for endpoint in self.endpoints:
            for cluster in endpoint.clusters:
                for attribute in cluster.attributes:
                    parameter = ZigbeeDataParameter(device_id, endpoint.endpoint_id, cluster.cluster_id, attribute.attribute_id, attribute.attribute_type)
                    parameters.append(parameter)

        return parameters


class ZigbeeUnsubscribeRequest:
    def __init__(self, endpointID: int, clusterID: int, attributeID: int, type: int):
        self.endpointID = endpointID
        self.clusterID = clusterID
        self.attributeID = attributeID
        self.type = type


class ZigbeeRegisterTopicRequest:
    endpointID: int
    clusterID: int
    attributeID: int
    type: int
