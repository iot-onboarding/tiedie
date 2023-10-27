# Copyright (c) 2023, Cisco and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

FROM eclipse-temurin:17-jdk-alpine AS build
WORKDIR /workspace/

COPY sample-java-app /workspace/sample-java-app
COPY sdk /workspace/sdk

WORKDIR /workspace/sample-java-app
RUN ./gradlew bootJar

FROM eclipse-temurin:17-jdk-alpine

ARG DEPENDENCY=/workspace/sample-java-app/build
WORKDIR /

COPY --from=build ${DEPENDENCY}/libs/*.jar app.jar

ENTRYPOINT ["java","-jar","/app.jar"]

