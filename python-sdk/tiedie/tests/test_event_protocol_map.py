#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""Tests for SDF event protocol maps."""

from tiedie.models.requests import (EventProtocolMap, GattEventProtocolMap,
                                    SdfModel, ZigbeeEventProtocolMap)
from tiedie.models.zigbee import ZigbeeEventType


def test_zigbee_attribute_reporting_event_protocol_map():
    """Test all fields in an attribute-reporting Zigbee event map."""
    protocol_map = EventProtocolMap(
        zigbee=ZigbeeEventProtocolMap(
            type=ZigbeeEventType.ATTRIBUTE_REPORTING,
            endpoint_id=1,
            cluster_id=1026,
            attribute_id=0,
            attribute_type=41,
            manufacturer_code=4151,
            min_reporting_interval=10,
            max_reporting_interval=300,
            reportable_change=50
        )
    )

    assert protocol_map.model_dump(
        by_alias=True, exclude_none=True, mode="json"
    ) == {
        "zigbee": {
            "endpointID": 1,
            "clusterID": 1026,
            "attributeID": 0,
            "attributeType": 41,
            "manufacturerCode": 4151,
            "profileID": 260,
            "type": "attribute_reporting",
            "minReportingInterval": 10,
            "maxReportingInterval": 300,
            "reportableChange": 50
        }
    }


def test_zigbee_write_event_protocol_map():
    """A write event defaults its profile and omits reporting options."""
    protocol_map = EventProtocolMap(
        zigbee=ZigbeeEventProtocolMap(
            type="write_event",
            endpoint_id=1,
            cluster_id=6,
            attribute_id=0,
            attribute_type=16
        )
    )

    assert protocol_map.model_dump(
        by_alias=True, exclude_none=True, mode="json"
    ) == {
        "zigbee": {
            "endpointID": 1,
            "clusterID": 6,
            "attributeID": 0,
            "attributeType": 16,
            "profileID": 260,
            "type": "write_event"
        }
    }


def test_zigbee_fractional_reportable_change():
    """A reportable change may be fractional for a Zigbee analog type."""
    protocol_map = ZigbeeEventProtocolMap(
        type="attribute_reporting",
        endpoint_id=1,
        cluster_id=1026,
        attribute_id=0,
        attribute_type=57,
        reportable_change=0.5
    )

    assert protocol_map.model_dump(by_alias=True, exclude_none=True)[
        "reportableChange"
    ] == 0.5


def test_ble_event_protocol_map_regression():
    """Existing direct BLE event maps retain their wire representation."""
    protocol_map = EventProtocolMap(
        ble=GattEventProtocolMap(
            type="gatt",
            service_id="1809",
            characteristic_id="2A1C"
        )
    )

    assert protocol_map.model_dump(
        by_alias=True, exclude_none=True, mode="json"
    ) == {
        "ble": {
            "type": "gatt",
            "serviceID": "1809",
            "characteristicID": "2A1C"
        }
    }


def test_zigbee_sdf_event_parsing():
    """A direct Zigbee event map can be parsed as part of an SDF model."""
    sdf_model = SdfModel.model_validate({
        "namespace": {"sensor": "https://example.com/sensor"},
        "defaultNamespace": "sensor",
        "sdfObject": {
            "temperatureSensor": {
                "sdfEvent": {
                    "temperatureChanged": {
                        "sdfProtocolMap": {
                            "zigbee": {
                                "type": "attribute_reporting",
                                "endpointID": 1,
                                "clusterID": 1026,
                                "attributeID": 0,
                                "attributeType": 41,
                                "minReportingInterval": 10,
                                "maxReportingInterval": 300,
                                "reportableChange": 50
                            }
                        }
                    }
                }
            }
        }
    })

    event_map = sdf_model.sdf_object[
        "temperatureSensor"
    ].sdf_event["temperatureChanged"].sdf_protocol_map.zigbee
    assert event_map is not None
    assert event_map.type == ZigbeeEventType.ATTRIBUTE_REPORTING
    assert event_map.profile_id == 260
