#!python
# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See accompanying LICENSE file in this distribution.

from typing import Union, List
from typing import Type
from .ble import *
from .zigbee import *
from .common import *


class TiedieBasicRequest:
    def __init__(self):
        self.technology = None
        self.uuid = None
        self.controlApp = None


    def __dict__(self):
        return {
            "technology": self.technology,
            "uuid": self.uuid,
            "controlApp": self.controlApp,
        }
    

    def __str__(self):
        return str(self.__dict__())
    
    
    def __json__(self):
        return self.__dict__()
    

    @staticmethod
    def create_request(device, control_app_id):
        tiedie_request = TiedieBasicRequest()
        tiedie_request.uuid = device.get("id")

        tiedie_request.controlApp = control_app_id

        if device.get("urn:ietf:params:scim:schemas:extension:ble:2.0:Device"):
            tiedie_request.technology = Technology.BLE.value
        elif device.get("urn:ietf:params:scim:schemas:extension:zigbee:2.0:Device"):
            tiedie_request.technology = Technology.ZIGBEE.value

        return tiedie_request
    

class TiedieReadRequest(TiedieBasicRequest):
    ble: Union[None, BleReadRequest] = None
    zigbee: Union[None, ZigbeeReadRequest] = None

    def __init__(self):
        super().__init__()
        self.ble = None
        self.zigbee = None


    def __dict__(self):
        return {
            "technology": self.technology,
            "uuid": self.uuid,
            "controlApp": self.controlApp,
            "ble": self.ble,
            "zigbee": self.zigbee,
        }
    
    
    def __str__(self):
        return str(self.__dict__())
    
    
    def __json__(self):
        return self.__dict__()
    

    @staticmethod
    def create_request(data_parameter, control_app_id):
        tiedie_request = TiedieReadRequest()
        tiedie_request.uuid = data_parameter.device_id
        tiedie_request.controlApp = control_app_id

        if isinstance(data_parameter, BleDataParameter):
            ble_data_parameter = data_parameter
            tiedie_request.technology = Technology.BLE
            ble_read_request = BleReadRequest(
                ble_data_parameter.serviceUUID, ble_data_parameter.charUUID
            )
            tiedie_request.ble = ble_read_request

        elif isinstance(data_parameter, ZigbeeDataParameter):
            zigbee_data_parameter = data_parameter
            tiedie_request.technology = Technology.ZIGBEE
            zigbee_read_request = ZigbeeReadRequest(
                zigbee_data_parameter.endpoint_id,
                zigbee_data_parameter.cluster_id,
                zigbee_data_parameter.attribute_id,
                zigbee_data_parameter.type_,
            )
            tiedie_request.zigbee = zigbee_read_request
        else:
            raise ValueError("Operation not supported for this device")

        return tiedie_request
    
    
class TiedieSubscribeRequest(TiedieBasicRequest):
    def __init__(self):
        super().__init__()
        self.topic = None
        self.data_format = None
        self.ble = None
        self.zigbee = None


    def __dict__(self):
        return {
            "technology": self.technology,
            "uuid": self.uuid,
            "controlApp": self.controlApp,
            "topic": self.topic,
            "dataFormat": self.data_format,
            "ble": self.ble,
            "zigbee": self.zigbee,
        }
    

    def __str__(self):
        return str(self.__dict__())
    

    @staticmethod
    def create_request(topic: str, data_parameter: DataParameter, control_app_id, options):
        if isinstance(data_parameter, BleDataParameter):
            return TiedieSubscribeRequest.create_request_for_ble(topic, data_parameter, control_app_id, options)

        if isinstance(data_parameter, ZigbeeDataParameter):
            return TiedieSubscribeRequest.create_request_for_zigbee(data_parameter, control_app_id, options)

        raise ValueError("Operation not supported for this device")


    @staticmethod
    def create_request_for_ble(topic: str, data_parameter: BleDataParameter, control_app_id, options=None):
        tiedie_request = TiedieSubscribeRequest()
        tiedie_request.topic = topic
        tiedie_request.uuid = data_parameter.device_id
        tiedie_request.controlApp = control_app_id
        tiedie_request.technology = Technology.BLE

        if options is None:
            options = SubscriptionOptions()

        tiedie_request.data_format = options.dataFormat or DataFormat.JSON
        tiedie_request.topic = options.topic

        ble_subscribe_request = BleSubscribeRequest(data_parameter.serviceUUID, data_parameter.charUUID)
        tiedie_request.ble = ble_subscribe_request

        return tiedie_request


    @staticmethod
    def create_request_for_zigbee(data_parameter: ZigbeeDataParameter, control_app_id, options):
        tiedie_request = TiedieSubscribeRequest()
        tiedie_request.uuid = data_parameter.device_id
        tiedie_request.controlApp = control_app_id
        tiedie_request.technology = Technology.ZIGBEE

        if options is None:
            options = SubscriptionOptions()

        tiedie_request.data_format = options.dataFormat or DataFormat.JSON
        tiedie_request.topic = options.topic

        zigbee_subscribe_request = ZigbeeSubscribeRequest(
            data_parameter.endpoint_id,
            data_parameter.cluster_id,
            data_parameter.attribute_id,
            data_parameter.type,
            options.min_report_time or 0,
            options.max_report_time or 60
        )
        tiedie_request.zigbee = zigbee_subscribe_request

        return tiedie_request


class TiedieWriteRequest(TiedieBasicRequest):
    def __init__(self):
        super().__init__()
        self.ble = None
        self.zigbee = None


    def __dict__(self):
        return {
            "technology": self.technology,
            "uuid": self.uuid,
            "controlApp": self.controlApp,
            "ble": self.ble,
            "zigbee": self.zigbee
        }


    def __str__(self):
        return str(self.__dict__())
    

    @staticmethod
    def create_request(data_parameter, value, control_app_id):
        tiedie_request = TiedieWriteRequest()
        tiedie_request.uuid = data_parameter.device_id
        tiedie_request.controlApp = control_app_id

        if isinstance(data_parameter, BleDataParameter):
            ble_data_parameter = data_parameter
            tiedie_request.technology = Technology.BLE
            ble_write_request = BleWriteRequest(
                ble_data_parameter.serviceUUID,
                ble_data_parameter.charUUID,
                value
            )
            tiedie_request.ble = ble_write_request

        elif isinstance(data_parameter, ZigbeeDataParameter):
            bytes_ = []
            for i in range(0, len(value), 2):
                s = value[i:i + 2]
                bytes_.append(int(s, 16))

            zigbee_data_parameter = data_parameter
            tiedie_request.technology = Technology.ZIGBEE
            zigbee_write_request = ZigbeeWriteRequest(
                zigbee_data_parameter.endpoint_id,
                zigbee_data_parameter.cluster_id,
                zigbee_data_parameter.attribute_id,
                zigbee_data_parameter.type,
                bytes_
            )
            tiedie_request.zigbee = zigbee_write_request

        else:
            raise ValueError("Operation not supported for this device")

        return tiedie_request
    

class TiedieConnectRequest(TiedieBasicRequest):
    def __init__(self):
        super().__init__()
        self.ble = None
    

    def __dict__(self):
        return {
            "uuid": self.uuid,
            "controlApp": self.controlApp,
            "technology": self.technology,
            "ble": self.ble.__dict__(),
        }
    
    def __str__(self):
        return str(self.__dict__())
    

    @staticmethod
    def create_request(device, request, control_app_id):
        tiedie_request = TiedieConnectRequest()
        tiedie_request.technology = Technology.BLE
        tiedie_request.uuid = device.get("id")
        tiedie_request.controlApp = control_app_id
        tiedie_request.ble = request
        return tiedie_request


class TiedieUnsubscribeRequest(TiedieBasicRequest):
    def __init__(self):
        super().__init__()
        self.ble = None
        self.zigbee = None

    
    def __dict__(self):
        return {
            "uuid": self.uuid,
            "controlApp": self.controlApp,
            "technology": self.technology,
            "ble": self.ble.__dict__(),
            "zigbee": self.zigbee.__dict__(),
        }
    
    
    def __str__(self):
        return str(self.__dict__())
    
    
    @classmethod
    def create_request(cls, dataParameter: DataParameter, controlAppId: str):
        if isinstance(dataParameter, BleDataParameter):
            bleDataParameter = dataParameter

            return cls.createBleRequest(bleDataParameter, controlAppId)

        if isinstance(dataParameter, ZigbeeDataParameter):
            zigbeeDataParameter = dataParameter

            return cls.createZigbeeRequest(zigbeeDataParameter, controlAppId)

        raise NotImplementedError("Operation not supported for this device")


    @classmethod
    def createBleRequest(cls, dataParameter: BleDataParameter, controlAppId: str):
        tiedieRequest = TiedieUnsubscribeRequest()
        tiedieRequest.uuid = dataParameter.getDeviceId()
        tiedieRequest.controlApp = controlAppId
        tiedieRequest.technology = Technology.BLE

        bleSubscribeRequest = BleUnsubscribeRequest(dataParameter.getServiceUUID(), dataParameter.getCharUUID())

        tiedieRequest.ble = bleSubscribeRequest

        return tiedieRequest


    @classmethod
    def createZigbeeRequest(cls, dataParameter: ZigbeeDataParameter, controlAppId: str):
        tiedieRequest = TiedieUnsubscribeRequest()
        tiedieRequest.uuid = dataParameter.getDeviceId()
        tiedieRequest.controlApp = controlAppId
        tiedieRequest.technology = Technology.ZIGBEE

        zigbeeSubscribeRequest = ZigbeeUnsubscribeRequest(
            dataParameter.getEndpointID(),
            dataParameter.getClusterID(),
            dataParameter.getAttributeID(),
            dataParameter.getType())

        tiedieRequest.zigbee = zigbeeSubscribeRequest

        return tiedieRequest


class TiedieRegisterTopicRequest(TiedieBasicRequest):
    uuids: List[str]
    topic: str
    data_format: DataFormat
    control_app: str
    ble: Type["BleRegisterTopicRequest"]
    zigbee: Type["ZigbeeRegisterTopicRequest"]


    def __init__(self):
        super().__init__()
        self.uuids = []
        self.topic = ""
        self.data_format = DataFormat.JSON
        self.control_app = ""
        self.ble = None
        self.zigbee = None
    

    def __json__(self):
        return {
            "uuids": self.uuids,
            "topic": self.topic,
            "data_format": self.data_format,
            "controlApp": self.control_app,
            "ble": self.ble,
            "zigbee": self.zigbee,
            "technology": self.technology
        }


    def __str__(self):
        return str(self.__dict__())
    

    @staticmethod
    def create_request(topic: str, options, control_app_id: str) -> "TiedieRegisterTopicRequest":
        tiedie_request = TiedieRegisterTopicRequest()

        tiedie_request.control_app = control_app_id
        tiedie_request.topic = topic
        tiedie_request.data_format = options.dataFormat

        if isinstance(options, DataRegistrationOptions):
            data_registration_options = options

            if isinstance(data_registration_options.dataParameter, BleDataParameter):
                parameter = data_registration_options.dataParameter
                tiedie_request.technology = Technology.BLE

                tiedie_request.uuids = [parameter.device_id]

                tiedie_request.ble = BleGattTopic(parameter.serviceUUID, parameter.charUUID)
            else:
                parameter = data_registration_options.dataParameter
                tiedie_request.technology = Technology.ZIGBEE
                tiedie_request.uuids = [parameter.device_id]
                tiedie_request.zigbee = ZigbeeRegisterTopicRequest(parameter.endpointID, parameter.clusterID, parameter.attributeID, parameter.type)
       
        elif isinstance(options, AdvertisementRegistrationOptions):
            advertisement_registration_options = options
            tiedie_request.technology = Technology.BLE
            tiedie_request.ble = BleAdvertisementTopic(advertisement_registration_options.advertisementFilterType, advertisement_registration_options.advertisementFilters)
        
        elif isinstance(options, ConnectionRegistrationOptions):
            tiedie_request.technology = Technology.BLE
            tiedie_request.ble = BleConnectionTopic()

        if options.devices is not None:
            tiedie_request.uuids = [device.deviceID for device in options.devices]
            
        return tiedie_request


class TiedieUnregisterTopicRequest(TiedieBasicRequest):
    def __init__(self):
        super().__init__()
        self.topic: str = None
        self.uuids: List[str] = []


    def __dict__(self):
        return {
            "topic": self.topic,
            "uuids": self.uuids,
            "controlApp": self.controlApp
        }


    def __str__(self):
        return str(self.__dict__())
    

    @staticmethod
    def create_request(topic: str, uuids: List[str], control_app_id: str):
        tiedie_request = TiedieUnregisterTopicRequest()

        tiedie_request.controlApp = control_app_id
        tiedie_request.uuids = uuids
        tiedie_request.topic = topic

        return tiedie_request


class TiedieRegisterDataAppRequest:
    def __init__(self, topic: str, dataApps:list(), controlApp: str) -> None:
        self.topic: str = topic
        self.data_apps:list() = dataApps
        self.control_app: str = controlApp
    

    def __dict__(self):
        return {
            "topic": self.topic,
            "dataApps": self.data_apps,
            "controlApp": self.control_app
        }
    
    
    def __str__(self):
        return str(self.__dict__())
    

    def __json__(self):
        return self.__dict__()


    @staticmethod
    def create_request(dataApp: str, topic: str, controlApp: str):
        return TiedieRegisterDataAppRequest(topic, [dataApp], controlApp)




