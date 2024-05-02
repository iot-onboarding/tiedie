from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DataSubscription(_message.Message):
    __slots__ = ["ap_macaddr", "ble_advertisement", "ble_connection_status", "ble_subscription", "data", "device_id", "raw_payload", "timestamp", "zigbee"]
    class BLEAdvertisement(_message.Message):
        __slots__ = ["mac_address", "rssi"]
        MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
        RSSI_FIELD_NUMBER: _ClassVar[int]
        mac_address: str
        rssi: int
        def __init__(self, mac_address: _Optional[str] = ..., rssi: _Optional[int] = ...) -> None: ...
    class BLEConnectionStatus(_message.Message):
        __slots__ = ["connected", "mac_address", "reason"]
        CONNECTED_FIELD_NUMBER: _ClassVar[int]
        MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
        REASON_FIELD_NUMBER: _ClassVar[int]
        connected: bool
        mac_address: str
        reason: int
        def __init__(self, mac_address: _Optional[str] = ..., connected: bool = ..., reason: _Optional[int] = ...) -> None: ...
    class BLESubscription(_message.Message):
        __slots__ = ["characteristic_uuid", "service_uuid"]
        CHARACTERISTIC_UUID_FIELD_NUMBER: _ClassVar[int]
        SERVICE_UUID_FIELD_NUMBER: _ClassVar[int]
        characteristic_uuid: str
        service_uuid: str
        def __init__(self, service_uuid: _Optional[str] = ..., characteristic_uuid: _Optional[str] = ...) -> None: ...
    class RawPayload(_message.Message):
        __slots__ = ["context_id"]
        CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
        context_id: str
        def __init__(self, context_id: _Optional[str] = ...) -> None: ...
    class ZigbeeSubscription(_message.Message):
        __slots__ = ["attribute_id", "attribute_type", "cluster_id", "endpoint_id"]
        ATTRIBUTE_ID_FIELD_NUMBER: _ClassVar[int]
        ATTRIBUTE_TYPE_FIELD_NUMBER: _ClassVar[int]
        CLUSTER_ID_FIELD_NUMBER: _ClassVar[int]
        ENDPOINT_ID_FIELD_NUMBER: _ClassVar[int]
        attribute_id: int
        attribute_type: int
        cluster_id: int
        endpoint_id: int
        def __init__(self, endpoint_id: _Optional[int] = ..., cluster_id: _Optional[int] = ..., attribute_id: _Optional[int] = ..., attribute_type: _Optional[int] = ...) -> None: ...
    AP_MACADDR_FIELD_NUMBER: _ClassVar[int]
    BLE_ADVERTISEMENT_FIELD_NUMBER: _ClassVar[int]
    BLE_CONNECTION_STATUS_FIELD_NUMBER: _ClassVar[int]
    BLE_SUBSCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    RAW_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ZIGBEE_FIELD_NUMBER: _ClassVar[int]
    ap_macaddr: str
    ble_advertisement: DataSubscription.BLEAdvertisement
    ble_connection_status: DataSubscription.BLEConnectionStatus
    ble_subscription: DataSubscription.BLESubscription
    data: bytes
    device_id: str
    raw_payload: DataSubscription.RawPayload
    timestamp: int
    zigbee: DataSubscription.ZigbeeSubscription
    def __init__(self, timestamp: _Optional[int] = ..., ap_macaddr: _Optional[str] = ..., device_id: _Optional[str] = ..., data: _Optional[bytes] = ..., ble_subscription: _Optional[_Union[DataSubscription.BLESubscription, _Mapping]] = ..., ble_advertisement: _Optional[_Union[DataSubscription.BLEAdvertisement, _Mapping]] = ..., zigbee: _Optional[_Union[DataSubscription.ZigbeeSubscription, _Mapping]] = ..., raw_payload: _Optional[_Union[DataSubscription.RawPayload, _Mapping]] = ..., ble_connection_status: _Optional[_Union[DataSubscription.BLEConnectionStatus, _Mapping]] = ...) -> None: ...
