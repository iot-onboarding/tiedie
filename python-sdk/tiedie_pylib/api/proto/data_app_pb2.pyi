from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DataSubscription(_message.Message):
    __slots__ = ["device_id", "data", "ble_subscription", "ble_advertisement", "zigbee", "raw_payload", "ble_connection_status"]
    class BLESubscription(_message.Message):
        __slots__ = ["service_uuid", "characteristic_uuid"]
        SERVICE_UUID_FIELD_NUMBER: _ClassVar[int]
        CHARACTERISTIC_UUID_FIELD_NUMBER: _ClassVar[int]
        service_uuid: str
        characteristic_uuid: str
        def __init__(self, service_uuid: _Optional[str] = ..., characteristic_uuid: _Optional[str] = ...) -> None: ...
    class BLEAdvertisement(_message.Message):
        __slots__ = ["mac_address", "rssi"]
        MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
        RSSI_FIELD_NUMBER: _ClassVar[int]
        mac_address: str
        rssi: int
        def __init__(self, mac_address: _Optional[str] = ..., rssi: _Optional[int] = ...) -> None: ...
    class ZigbeeSubscription(_message.Message):
        __slots__ = ["endpoint_id", "cluster_id", "attribute_id", "attribute_type"]
        ENDPOINT_ID_FIELD_NUMBER: _ClassVar[int]
        CLUSTER_ID_FIELD_NUMBER: _ClassVar[int]
        ATTRIBUTE_ID_FIELD_NUMBER: _ClassVar[int]
        ATTRIBUTE_TYPE_FIELD_NUMBER: _ClassVar[int]
        endpoint_id: int
        cluster_id: int
        attribute_id: int
        attribute_type: int
        def __init__(self, endpoint_id: _Optional[int] = ..., cluster_id: _Optional[int] = ..., attribute_id: _Optional[int] = ..., attribute_type: _Optional[int] = ...) -> None: ...
    class BLEConnectionStatus(_message.Message):
        __slots__ = ["mac_address", "connected", "reason"]
        MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
        CONNECTED_FIELD_NUMBER: _ClassVar[int]
        REASON_FIELD_NUMBER: _ClassVar[int]
        mac_address: str
        connected: bool
        reason: int
        def __init__(self, mac_address: _Optional[str] = ..., connected: bool = ..., reason: _Optional[int] = ...) -> None: ...
    class RawPayload(_message.Message):
        __slots__ = ["context_id"]
        CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
        context_id: str
        def __init__(self, context_id: _Optional[str] = ...) -> None: ...
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    BLE_SUBSCRIPTION_FIELD_NUMBER: _ClassVar[int]
    BLE_ADVERTISEMENT_FIELD_NUMBER: _ClassVar[int]
    ZIGBEE_FIELD_NUMBER: _ClassVar[int]
    RAW_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    BLE_CONNECTION_STATUS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    data: bytes
    ble_subscription: DataSubscription.BLESubscription
    ble_advertisement: DataSubscription.BLEAdvertisement
    zigbee: DataSubscription.ZigbeeSubscription
    raw_payload: DataSubscription.RawPayload
    ble_connection_status: DataSubscription.BLEConnectionStatus
    def __init__(self, device_id: _Optional[str] = ..., data: _Optional[bytes] = ..., ble_subscription: _Optional[_Union[DataSubscription.BLESubscription, _Mapping]] = ..., ble_advertisement: _Optional[_Union[DataSubscription.BLEAdvertisement, _Mapping]] = ..., zigbee: _Optional[_Union[DataSubscription.ZigbeeSubscription, _Mapping]] = ..., raw_payload: _Optional[_Union[DataSubscription.RawPayload, _Mapping]] = ..., ble_connection_status: _Optional[_Union[DataSubscription.BLEConnectionStatus, _Mapping]] = ...) -> None: ...