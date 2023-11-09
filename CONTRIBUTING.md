<!--
Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
All rights reserved.
See LICENSE file in this distribution.
SPDX-License-Identifier: Apache-2.0
-->

# Contributing to Tie Die

## Reporting issues.

We would be very pleased to hear of issues relating to the code.  You
may report issues by opening a Github issue.

## Suggestions for new features

You may suggest new features, provided that you are unaware of any
intellectual property entanglements, and they can be added in accordance
with the license.

## Creating a development environment

The Java SDK requires Java.  See the java-sdk directory for details.
The Python SDK requires Python 3.  See the python-sdk directory for details.
The Gateway requires Python 3.  See the Gateway directory for details.

In all cases, a BLE device is required, and you should know how to control
it.  Tiedie aims to provide access, but does not have any understanding of
device semantics.

## Adding New Code

We gladly accept PRs for new code after some review.  We have limited
CI/CD capability due to the nature of the project (you have to have
devices with which to test).  Any new functionality should of course not
disrupt old functionality.

## Changing Old Code

This is new code.  We expect that there will be a number of bugs.  We
welcome cleanup.

Generally speaking, a PR should be clear on what it intends.  File changes
should be limited to that intent.  Major changes will of course get more
attention.  It may be advisable to open an issue, to start discussion
prior to the PR.
