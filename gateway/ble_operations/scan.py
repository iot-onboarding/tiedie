# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See license in distribution for details.

from ble_operations.operation import Operation

from data_producer import DataProducer


class ScanOperation(Operation):
    def __init__(self, lib, data_producer: DataProducer):
        super().__init__(lib)
        self.data_producer = data_producer

    def run(self):
        """ Start scanning """
        self.lib.bt.scanner.start(  # type: ignore
            self.lib.bt.scanner.SCAN_PHY_SCAN_PHY_1M,  # type: ignore
            self.lib.bt.scanner.DISCOVER_MODE_DISCOVER_GENERIC)  # type: ignore

    def __stop_scan(self):
        """ Stop scanning """
        self.lib.bt.scanner.stop()  # type: ignore

    def bt_evt_scanner_scan_report(self, evt):
        self.log.debug(evt)
        self.handle_advertisement(evt)

    def bt_evt_scanner_legacy_advertisement_report(self, evt):
        self.log.debug(evt)
        self.handle_advertisement(evt)

    def handle_advertisement(self, evt):
        self.data_producer.publish_advertisement(evt)

    def __repr__(self):
        return f"ScanOperation()"
