from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DataSubscription(_message.Message):
    __slots__ = ["ble_advertisement", "ble_subscription", "data", "device_id", "zigbee"]
    class BLEAdvertisement(_message.Message):
        __slots__ = ["mac_address", "rssi"]
        MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
        RSSI_FIELD_NUMBER: _ClassVar[int]
        mac_address: str
        rssi: int
        def __init__(self, mac_address: _Optional[str] = ..., rssi: _Optional[int] = ...) -> None: ...
    class BLESubscription(_message.Message):
        __slots__ = ["characteristic_uuid", "service_uuid"]
        CHARACTERISTIC_UUID_FIELD_NUMBER: _ClassVar[int]
        SERVICE_UUID_FIELD_NUMBER: _ClassVar[int]
        characteristic_uuid: str
        service_uuid: str
        def __init__(self, service_uuid: _Optional[str] = ..., characteristic_uuid: _Optional[str] = ...) -> None: ...
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
    BLE_ADVERTISEMENT_FIELD_NUMBER: _ClassVar[int]
    BLE_SUBSCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    ZIGBEE_FIELD_NUMBER: _ClassVar[int]
    ble_advertisement: DataSubscription.BLEAdvertisement
    ble_subscription: DataSubscription.BLESubscription
    data: bytes
    device_id: str
    zigbee: DataSubscription.ZigbeeSubscription
    def __init__(self, device_id: _Optional[str] = ..., data: _Optional[bytes] = ..., ble_subscription: _Optional[_Union[DataSubscription.BLESubscription, _Mapping]] = ..., ble_advertisement: _Optional[_Union[DataSubscription.BLEAdvertisement, _Mapping]] = ..., zigbee: _Optional[_Union[DataSubscription.ZigbeeSubscription, _Mapping]] = ...) -> None: ...
