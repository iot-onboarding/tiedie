# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

FROM eclipse-temurin:17-jdk-alpine

WORKDIR /

COPY build/libs/*.jar app.jar

ENTRYPOINT ["java","-jar","/app.jar"]

