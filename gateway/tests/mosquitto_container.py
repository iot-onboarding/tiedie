# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

""" MosquittoContainer class. """

from typing import List, Optional
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_container_is_ready, wait_for_logs
import paho.mqtt.client as mqtt


class MosquittoContainer(DockerContainer):
    """ Test container for Mosquitto. """

    def __init__(
            self,
            image: str = "eclipse-mosquitto:latest",
            port: Optional[int] = 1883,
            volume_mappings: List[tuple[str, str]] = None
    ):
        super().__init__(image)
        self.port = port
        self.with_exposed_ports(self.port)
        if volume_mappings is None:
            volume_mappings = []
        for host, container in volume_mappings:
            self.with_volume_mapping(host, container)

    @wait_container_is_ready()
    def readiness_probe(self) -> bool:
        """ Check if the container is ready. """
        wait_for_logs(self, "mosquitto version .* running")

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.username_pw_set("test", "test")
        client.connect(self.get_container_host_ip(), int(self.get_exposed_port(self.port)), 60)
        client.loop(timeout=1.0)

        if client.is_connected():
            client.disconnect()
            client.loop_stop()
            return self

        raise RuntimeError("Failed to connect to Mosquitto")

    def start(self) -> "MosquittoContainer":
        """ Start the test container. """
        super().start()
        self.readiness_probe()
        return self
