#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""
These classes are designed for structured communication with the
Tiedie IoT platform.  They enable the creation of requests for
reading, subscribing, writing, and managing topics for IoT devices
using BLE and Zigbee technologies.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field
from pydantic.alias_generators import to_camel
from tiedie.models.ble import (AdvertisementRegistrationOptions,
                               BleAdvertisementTopic,
                               BleConnectRequest,
                               BleConnectionTopic,
                               BleDataParameter,
                               BleGattTopic,
                               BleReadRequest)
from tiedie.models.common import (ConnectionRegistrationOptions, DataApp,
                                  DataFormat,
                                  DataParameter,
                                  DataRegistrationOptions,
                                  RegistrationOptions,
                                  Technology)

from tiedie.models.scim import Device
from tiedie.models.zigbee import ZigbeeDataParameter, ZigbeeReadRequest, ZigbeeRegisterTopicRequest


class TiedieBasicRequest(BaseModel):
    """ 
    Base class for all Tiedie requests. It includes common attributes
    like technology, UUID, and control application. 
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    device: Optional[Device] = Field(exclude=True, default=None)

    @computed_field
    @property
    def technology(self) -> Optional[Technology]:
        """ Returns the technology used by the device. """
        if self.device is not None and self.device.ble_extension is not None:  # pylint: disable=no-member
            return Technology.BLE

        if self.device is not None and self.device.zigbee_extension is not None:  # pylint: disable=no-member
            return Technology.ZIGBEE

        return None

    @computed_field(alias="id")
    @property
    def device_id(self) -> Optional[str]:
        """ Returns the ID of the device. """
        if self.device is None:
            return None
        return self.device.device_id  # pylint: disable=no-member


class TiedieReadRequest(TiedieBasicRequest):
    """
    A request for reading data from IoT devices, with support for both
    BLE and Zigbee technologies. 
    """

    data_parameter: DataParameter = Field(exclude=True)

    @computed_field
    @property
    def ble(self) -> Optional[BleReadRequest]:
        """ Returns the BLE read request. """
        if self.technology == Technology.BLE and \
                isinstance(self.data_parameter, BleDataParameter):
            return BleReadRequest(
                service_id=self.data_parameter.service_id,  # pylint: disable=no-member
                characteristic_id=self.data_parameter.characteristic_id  # pylint: disable=no-member
            )

        return None

    @computed_field
    @property
    def zigbee(self) -> Optional[ZigbeeReadRequest]:
        """ Returns the Zigbee read request. """
        if self.technology == Technology.ZIGBEE and \
                isinstance(self.data_parameter, ZigbeeDataParameter):
            return ZigbeeReadRequest(
                endpoint_id=self.data_parameter.endpoint_id,  # pylint: disable=no-member
                cluster_id=self.data_parameter.cluster_id,  # pylint: disable=no-member
                attribute_id=self.data_parameter.attribute_id,  # pylint: disable=no-member
                type=self.data_parameter.attribute_type  # pylint: disable=no-member
            )

        return None


class TiedieWriteRequest(TiedieReadRequest):
    """
    A request class for writing data to IoT devices, supporting both
    BLE and Zigbee technologies.
    """

    value: str


class TiedieConnectRequest(TiedieBasicRequest):
    """
    A request class for establishing a connection with BLE devices,
    primarily used for BLE technology.
    """
    ble: BleConnectRequest
    retries: Optional[int] = 3
    retry_multiple_aps: Optional[bool] = Field(alias=str("retryMultipleAPs"), default=True)


class TiedieRegisterTopicRequest(TiedieBasicRequest):
    """ A request class for registering topic to IoT devices. """

    registration_options: Optional[RegistrationOptions] = Field(
        exclude=True, default=None)

    event: str

    @computed_field
    @property
    def technology(self) -> Optional[Technology]:
        if super().technology is not None:
            return super().technology

        if isinstance(self.registration_options,
                      (AdvertisementRegistrationOptions | ConnectionRegistrationOptions)):
            return Technology.BLE

        return Technology.ZIGBEE

    @computed_field(alias="dataApps")
    @property
    def data_apps(self) -> Optional[List[DataApp]]:
        """ Returns the data apps. """
        if self.registration_options is not None and \
                self.registration_options.data_apps is not None:
            return [
                DataApp(data_app_id=data_app_id)
                for data_app_id in self.registration_options.data_apps  # pylint: disable=no-member
            ]
        return None

    @computed_field(alias="dataFormat")
    @property
    def data_format(self) -> Optional[DataFormat]:
        """ Returns the data format. """
        if self.registration_options is not None:
            return self.registration_options.data_format  # pylint: disable=no-member
        return None

    @computed_field
    @property
    def ble(self) -> Optional[BleGattTopic | BleAdvertisementTopic | BleConnectionTopic]:
        """ Returns the BLE register topic request. """
        if self.technology == Technology.BLE and \
                isinstance(self.registration_options, DataRegistrationOptions) and \
                isinstance(self.registration_options.data_parameter, BleDataParameter):  # pylint: disable=no-member
            return BleGattTopic(
                service_id=self.registration_options.data_parameter.service_id,  # pylint: disable=no-member
                characteristic_id=self.registration_options.data_parameter.characteristic_id,  # pylint: disable=no-member
            )
        if isinstance(self.registration_options, AdvertisementRegistrationOptions):  # pylint: disable=no-member
            return BleAdvertisementTopic(
                filters=self.registration_options.advertisement_filter,  # pylint: disable=no-member
                filter_type=self.registration_options.advertisement_filter_type  # pylint: disable=no-member
            )

        if isinstance(self.registration_options, ConnectionRegistrationOptions):
            return BleConnectionTopic()

        return None

    @computed_field
    @property
    def zigbee(self) -> Optional[ZigbeeRegisterTopicRequest]:
        """ Returns the Zigbee register topic request. """
        if self.technology == Technology.ZIGBEE and \
                isinstance(self.registration_options, DataRegistrationOptions) and \
                isinstance(self.registration_options.data_parameter, ZigbeeDataParameter):  # pylint: disable=no-member
            return ZigbeeRegisterTopicRequest(
                endpoint_id=self.registration_options.data_parameter.endpoint_id,  # pylint: disable=no-member
                cluster_id=self.registration_options.data_parameter.cluster_id,  # pylint: disable=no-member
                attribute_id=self.registration_options.data_parameter.attribute_id,  # pylint: disable=no-member
                attribute_type=self.registration_options.data_parameter.attribute_type  # pylint: disable=no-member
            )

        return None


class IDQuery(BaseModel):
    """ Object with device ID used for query parameter generation """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    device_ids: List[Optional[str]] = Field(alias=str("id"))


class TopicQuery(BaseModel):
    """ Object with topic used for query parameter generation """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    event: str
