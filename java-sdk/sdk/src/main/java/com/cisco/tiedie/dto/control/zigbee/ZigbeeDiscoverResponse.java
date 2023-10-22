// Copyright (c) 2023, Cisco and/or its affiliates.
// All rights reserved.
// See license in distribution for details.

package com.cisco.tiedie.dto.control.zigbee;

import com.cisco.tiedie.dto.control.DataParameter;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class ZigbeeDiscoverResponse {
    private List<Endpoint> endpoints;

    public List<DataParameter> toParameterList(String deviceId) {
        List<DataParameter> parameters = new ArrayList<>();

        for (Endpoint endpoint : endpoints) {
            for (Cluster cluster : endpoint.clusters) {
                for (Attribute attribute : cluster.attributes) {
                    var parameter = new ZigbeeDataParameter();
                    parameter.setDeviceId(deviceId);
                    parameter.setEndpointID(endpoint.endpointId);
                    parameter.setClusterID(cluster.clusterId);
                    parameter.setAttributeID(attribute.attributeId);
                    parameter.setType(attribute.attributeType);

                    parameters.add(parameter);
                }
            }
        }

        return parameters;
    }

    @Data
    private static class Endpoint {
        private Integer endpointId;

        private List<Cluster> clusters;
    }

    @Data
    private static class Cluster {
        private Integer clusterId;
        private List<Attribute> attributes;
    }

    @Data
    private static class Attribute {
        private Integer attributeId;
        private Integer attributeType;
    }
}
