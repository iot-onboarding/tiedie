"""
Mock AccessPoint class
"""

import dataclasses
from http import HTTPStatus
import random
import threading
import time
import uuid
from flask import Response, jsonify
from access_point import AccessPoint, ConnectionRequest
from data_producer import DataProducer

mock_advertisements = [
    "02010620074dcb76a1591f4c868f42279d96eac57f",
    "02011a020a0c16ff4c001007721f41b0392078",
    "02011a020a0614ff4c0010063d1a1b72f249",
    "02011a32ff4c000c0e003423406bf3b0679f9c66a0662e1005711cea886b",
    "02010632ff4c00021574278bdab64445208f0c720eaf0599350000e2eec5",
    "02011a2cff4c00090813910a00003a1b5813080aa41953605b0a00",
    "02010632ff4c00021574278bdab64445208f0c720eaf05993500009732c5",
    "02011a020a0b12ff4c001005331ce25024",
    "02011a32ff4c000c0e00fc87017a6770f6d7e588b042ad10054b1c148d39",
    "02011a34ff75004204010167808abd47a827828abd47a8269d000000000000",
    "02011a2cff4c00090813e30a0000aa1b5813080a9ccf3bed321c00",
    "02011a020a1114ff4c0010060d1dd2274638",
    "0201062007b75c49d204a34071a0b535853eb083071009594c20436f6c6f72",
    "0201062007089119b580b99bb4ea4081d1521d1c300c094d3248533131",
    "0201020403b8fe",
    "02011a020a0912ff4c001005229837fcb4",
    "02011a020a1114ff4c001006091d52808d28",
    "02011a020a0c14ff4c001006081daeb9d138",
    "02011a18ff4c0013081ac0e21124ef5700",
    "02011a020a0712ff4c001005451c1654d1",
    "02011a020a0614ff4c001006351e55add483",
    "02011a18ff4c00090813800a0000771b58",
    "02011a020a0814ff4c001006351ede455d30",
    "02010632ff4c00021574278bdab64445208f0c720eaf0599350000bc32c5",
    "02010604027bfd18ff70080702d03f27609e0a0101",
    "0201060403a0fe1e16a0fe03fa8fca5121db653030332fff",
    "020116020a0018ff423043303930443830433937",
    "02011a020a0b16ff4c001007361fd8c9d42b48",
    "02011a020a0c12ff4c0010051e18b6c478",
    "02011a020a051aff4c000f059000aeb1bc10022704",
    "02011a020a0c12ff4c001005051473882b",
    "02010620074ecb76a1591f4c868f42279d96eac57f0c094d3248533131",
    "02011a020a0c14ff4c001006141a5d9bddb9",
    "02011a020a1112ff4c0010051c1c57449b",
    "02011a020a0716ff4c001007311fb635fb3a08",
    "02011a020a0812ff4c0010052518ec5c7a",
    "0201063016f7fd013ebe0c568af35f8f67fe5cbc937539ea0000000003",
    "02010626094e616e6f6c656166205374726970203156314b",
    "02011a020a0c12ff4c001005011490e205",
    "02011a020a061aff4c000f0590002e1fd410022d04",
    "0201062009416e7943617374203238303546313845",
    "02010632ff4c00021574278bdab64445208f0c720eaf0599350000b33bc5",
    "02011a020a0c14ff4c001006721e696ba852"
]


@dataclasses.dataclass
class Advertisement:
    """ Advertisement class for publishing """
    address: str
    rssi: int
    data: bytes


@dataclasses.dataclass
class ConnectionEvent:
    """ Mock connection event """
    reason: int


class MockAccessPoint(AccessPoint):
    """ Mock AccessPoint class"""

    scan_thread: threading.Thread

    def __init__(self, data_producer: DataProducer):
        super().__init__(data_producer)
        self._scanning = False
        self._subscription_threads: dict[(
            str, str, str), threading.Thread] = {}

    def start(self):
        self.log.info("System booted")
        self.ready.set()

    def stop(self):
        self.log.info("Stopping...")
        self._scanning = False
        self.scan_thread.join()

    def connectable(self):
        return True

    def start_scan(self):
        # Generate advertisement events
        self._scanning = True
        self.scan_thread = threading.Thread(target=self._send_scan_data)
        self.scan_thread.start()

    def _send_scan_data(self):
        while self._scanning:
            i = 0
            for adv in mock_advertisements:
                self.data_producer.publish_advertisement(
                    Advertisement(
                        f"C1:5C:00:00:00:{i:02}",
                        random.randint(-30, -20),
                        bytes.fromhex(adv)
                    )
                )
                i += 1

    def connect(self, address, services, retries=3) -> tuple[Response, int]:
        if not self.connectable():
            return jsonify({
                "status": "FAILURE",
                "requestID": uuid.uuid4(),
                "reason": "max connections"
            }), HTTPStatus.BAD_REQUEST

        if address in self.conn_reqs:
            return jsonify({
                "status": "FAILURE",
                "requestID": uuid.uuid4(),
                "reason": "already connected"
            }), HTTPStatus.BAD_REQUEST

        self.conn_reqs[address] = ConnectionRequest(address, 0, {})
        self.data_producer.publish_connection_status(
            ConnectionEvent(0), address, True)

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4(),
            "services": [
                {
                    "serviceID": "180d",
                    "characteristics": [
                        {
                            "characteristicID": "2a37",
                            "flags": ["notify"],
                            "descriptors": [
                                {
                                    "descriptorID": "2902"
                                }
                            ]
                        },
                        {
                            "characteristicID": "2a38",
                            "flags": ["read"]
                        },
                        {
                            "characteristicID": "2a39",
                            "flags": ["write"]
                        }
                    ]
                }
            ]
        }), HTTPStatus.OK

    def discover(self, address, retries) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4(),
            "services": [
                {
                    "serviceID": "180d",
                    "characteristics": [
                        {
                            "characteristicID": "2a37",
                            "flags": ["notify"],
                            "descriptors": [
                                {
                                    "descriptorID": "2902"
                                }
                            ]
                        },
                        {
                            "characteristicID": "2a38",
                            "flags": ["read"]
                        },
                        {
                            "characteristicID": "2a39",
                            "flags": ["write"]
                        }
                    ]
                }
            ]
        }), HTTPStatus.OK

    def read(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        if service_uuid != "180d" or char_uuid != "2a38":
            return jsonify({
                "status": "FAILURE",
                "reason": "Invalid service or characteristic uuid"
            }), HTTPStatus.BAD_REQUEST

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4(),
            "value": "000001"
        }), HTTPStatus.OK

    def write(self,
              address: str,
              service_uuid: str,
              char_uuid: str,
              value: str) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        if service_uuid != "180d" or char_uuid != "2a39":
            return jsonify({
                "status": "FAILURE",
                "reason": "Invalid service or characteristic uuid"
            }), HTTPStatus.BAD_REQUEST

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4(),
            "value": value
        }), HTTPStatus.OK

    def subscribe(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        thread = threading.Thread(
            target=self._send_subscribe_data, args=(address, service_uuid, char_uuid))
        thread.start()

        self._subscription_threads[(address, service_uuid, char_uuid)] = thread

        return jsonify({"status": "SUCCESS", "requestID": uuid.uuid4()}), HTTPStatus.OK

    def unsubscribe(self, address: str, service_uuid: str, char_uuid: str) -> tuple[Response, int]:
        thread = self._subscription_threads[(address, service_uuid, char_uuid)]
        self._subscription_threads.pop((address, service_uuid, char_uuid))
        thread.join()

        return jsonify({"status": "SUCCESS", "requestID": uuid.uuid4()}), HTTPStatus.OK

    def _send_subscribe_data(self, address, service_uuid, char_uuid):
        while (address, service_uuid, char_uuid) in self._subscription_threads:
            self.data_producer.publish_notification(
                address,
                service_uuid,
                char_uuid,
                (0xFFFF0000 + random.randint(0, 0xFFFF)).to_bytes(4)
            )
            time.sleep(1)

    def disconnect(self, address: str) -> tuple[Response, int]:
        if address not in self.conn_reqs:
            return jsonify({"status": "FAILURE", "reason": "not connected"}), HTTPStatus.BAD_REQUEST

        self.conn_reqs.pop(address)
        self.data_producer.publish_connection_status(
            ConnectionEvent(1), address, False)

        return jsonify({
            "status": "SUCCESS",
            "requestID": uuid.uuid4()
        }), HTTPStatus.OK
