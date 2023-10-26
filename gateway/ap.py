""" Helper module for creating BLE AP object """

from access_point import AccessPoint
from data_producer import DataProducer
from mock.mock_access_point import MockAccessPoint
from silabs.common.util import get_connector
from silabs.silabs_access_point import SilabsAccessPoint


_ble_ap: AccessPoint = None  # type: ignore


def create_ble_ap(data_producer: DataProducer) -> AccessPoint:
    """ function to create BLE AP """
    global _ble_ap  # pylint: disable=global-statement
    connector = get_connector()
    if connector is None:
        _ble_ap = MockAccessPoint(data_producer)
    else:
        _ble_ap = SilabsAccessPoint(connector, data_producer)
    return _ble_ap


def ble_ap() -> AccessPoint:
    """ Global BLE AP getter """
    return _ble_ap
