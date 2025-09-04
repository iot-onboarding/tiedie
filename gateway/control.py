# Copyright (c) 2023, Cisco Systems, Inc. and/or its affiliates.
# All rights reserved.
# See LICENSE file in this distribution.
# SPDX-License-Identifier: Apache-2.0

"""

This module creates a Flask Blueprint for controlling Bluetooth Low
Energy (BLE) devices, handling connections, data operations, and topic
registrations with authentication.

"""

import base64
import logging
import urllib.parse
from http import HTTPStatus
from functools import wraps
from enum import Enum
import uuid
import werkzeug.serving
import OpenSSL
from flask import Blueprint, jsonify, make_response, request
from sqlalchemy import select
from ap_factory import ble_ap
from database import session
from access_point_responses import (
    BleConnectionError,
    BleDisconnectError,
    BleDiscoveryError,
    BleReadError,
    BleWriteError
)
from access_point import BleConnectOptions
from models import Device, EndpointApp
from nipc_models import BleExtension, DataApp, SdfModel, Event
from tiedie_exceptions import SchemaError

# NIPC Problem Details Error Types Constants
class NipcProblemTypes(str, Enum):
    """
    NIPC Problem Details error types as defined in the NIPC draft
    (https://datatracker.ietf.org/doc/html/draft-ietf-asdf-nipc-12) 
    Section 6 and IANA registry Section 10.4.
    """
    # Base URI for IANA HTTP Problem Types registry
    _IANA_BASE = "https://www.iana.org/assignments/nipc-problem-types#"

    # Generic errors
    INVALID_ID = _IANA_BASE + "invalid-id"
    INVALID_SDF_URL = _IANA_BASE + "invalid-sdf-url"
    EXTENSION_OPERATION_NOT_EXECUTED = _IANA_BASE + "extension-operation-not-executed"
    SDF_MODEL_ALREADY_REGISTERED = _IANA_BASE + "sdf-model-already-registered"
    SDF_MODEL_IN_USE = _IANA_BASE + "sdf-model-in-use"

    # Property API errors
    PROPERTY_NOT_READABLE = _IANA_BASE + "property-not-readable"
    PROPERTY_NOT_WRITABLE = _IANA_BASE + "property-not-writable"

    # Event API errors
    EVENT_ALREADY_ENABLED = _IANA_BASE + "event-already-enabled"
    EVENT_NOT_ENABLED = _IANA_BASE + "event-not-enabled"
    EVENT_NOT_REGISTERED = _IANA_BASE + "event-not-registered"

    # Protocol specific errors - BLE
    PROTOCOLMAP_BLE_ALREADY_CONNECTED = _IANA_BASE + "protocolmap-ble-already-connected"
    PROTOCOLMAP_BLE_NO_CONNECTION = _IANA_BASE + "protocolmap-ble-no-connection"
    PROTOCOLMAP_BLE_CONNECTION_TIMEOUT = _IANA_BASE + "protocolmap-ble-connection-timeout"
    PROTOCOLMAP_BLE_BONDING_FAILED = _IANA_BASE + "protocolmap-ble-bonding-failed"
    PROTOCOLMAP_BLE_CONNECTION_FAILED = _IANA_BASE + "protocolmap-ble-connection-failed"
    PROTOCOLMAP_BLE_SERVICE_DISCOVERY_FAILED = _IANA_BASE + \
        "protocolmap-ble-service-discovery-failed"
    PROTOCOLMAP_BLE_INVALID_SERVICE_OR_CHARACTERISTIC = _IANA_BASE + \
        "protocolmap-ble-invalid-service-or-characteristic"

    # Protocol specific errors - Zigbee
    PROTOCOLMAP_ZIGBEE_CONNECTION_TIMEOUT = \
        _IANA_BASE + "protocolmap-zigbee-connection-timeout"
    PROTOCOLMAP_ZIGBEE_INVALID_ENDPOINT_OR_CLUSTER = \
        _IANA_BASE + "protocolmap-zigbee-invalid-endpoint-or-cluster"

    # Extension API errors
    EXTENSION_BROADCAST_INVALID_DATA = _IANA_BASE + "extension-broadcast-invalid-data"
    EXTENSION_FIRMWARE_ROLLBACK = _IANA_BASE + "extension-firmware-rollback"
    EXTENSION_FIRMWARE_UPDATE_FAILED = _IANA_BASE + "extension-firmware-update-failed"

    # RFC 9457 generic error for internal server errors
    ABOUT_BLANK = "about:blank"

control_app = Blueprint("control", __name__, url_prefix="/nipc")


def create_nipc_problem_response(
    error_type: NipcProblemTypes,
    status: HTTPStatus,
    title: str,
    detail: str
) -> tuple:
    """Create a NIPC Problem Details response.
    
    Args:
        error_type: NIPC Problem Details error type
        status: HTTP status code
        title: Brief error summary
        detail: Detailed error description
    
    Returns:
        tuple of (response_dict, status_code)
    """
    response = {
        "type": error_type.value,
        "status": status.value,
        "title": title,
        "detail": detail
    }
    return jsonify(response), status


class PeerCertWSGIRequestHandler(werkzeug.serving.WSGIRequestHandler):
    """Custom WSGI request handler to extract and provide peer certificates."""

    def make_environ(self):
        environ = super().make_environ()
        x509_binary = self.connection.getpeercert(True)
        if x509_binary is None:
            environ['peercert'] = None
            return environ
        x509 = OpenSSL.crypto.load_certificate(  # type: ignore
            OpenSSL.crypto.FILETYPE_ASN1, x509_binary)  # type: ignore
        environ['peercert'] = x509
        return environ


def authenticate_user(func):
    """Verify x-api-key or client certificate."""

    @wraps(func)
    def check_apikey(*args, **kwargs):
        client_cert: OpenSSL.crypto.X509 | None = request.environ.get(
            'peercert')
        if client_cert:
            endpoint_app = session.scalar(
                select(EndpointApp)
                .filter_by(subjectName=client_cert.get_subject().CN)
            )
            if endpoint_app is not None:
                return func(*args, **kwargs)

            return make_response(jsonify({"error": "Unauthorized"}), 403)

        api_key = request.headers.get("X-Api-Key")
        if api_key is None:
            return make_response(jsonify({"error": "Unauthorized"}), 403)

        endpoint_app = session.scalar(select(EndpointApp).
                                      filter_by(clientToken=api_key))

        if endpoint_app is None:
            return make_response(jsonify({"error": "Unauthorized"}), 403)

        return func(*args, **kwargs)
    return check_apikey


@control_app.route('/devices/<device_id>/connections', methods=['POST'])
@authenticate_user
def connect(device_id: str):
    """Connect to a device (NIPC Section 4.4.1)."""
    device = session.get(BleExtension, device_id)
    if device is None:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_ID,
            HTTPStatus.NOT_FOUND,
            "Not Found",
            f"Device ID {device_id} does not exist or is not a device"
        )

    # Default connection parameters
    retries = 3
    retry_multiple_aps = True
    services = []
    cached = False
    cache_idle_purge = 3600
    auto_update = True
    bonding = "default"

    # Parse request body if provided
    if request.is_json and request.get_json():
        retries = request.get_json().get("retries", retries)
        retry_multiple_aps = request.get_json().get("retryMultipleAPs", retry_multiple_aps)

        protocol_map = request.get_json().get("sdfProtocolMap", {})
        ble_config = protocol_map.get("ble", {})
        if ble_config:
            services = ble_config.get("services", [])
            cached = bool(ble_config.get("cached", cached))
            cache_idle_purge = int(ble_config.get("cacheIdlePurge", cache_idle_purge))
            auto_update = bool(ble_config.get("autoUpdate", auto_update))
            bonding = str(ble_config.get("bonding", bonding))

    try:
        connect_options = BleConnectOptions(services, cached, cache_idle_purge)
        ble_ap().connect(
            device.device_mac_address,
            connect_options,
            retries
        )

        discover_result = ble_ap().discover(
            device.device_mac_address,
            connect_options,
            retries
        )

        response_data = {
            "id": device_id,
            "sdfProtocolMap": {
                "ble": [
                    {
                        "serviceID": svc.service_id,
                        "characteristics": [
                            {
                                "characteristicID": char.characteristic_id,
                                "flags": char.properties,
                                "descriptors": char.descriptors
                            }
                            for char in svc.characteristics.values()
                        ]
                    }
                    for svc in discover_result.services
                ]
            }
        }
        return jsonify(response_data), HTTPStatus.OK
    except (BleConnectionError, BleDiscoveryError) as e:
        return create_nipc_problem_response(
            NipcProblemTypes.PROTOCOLMAP_BLE_NO_CONNECTION,
            HTTPStatus.BAD_REQUEST,
            "Connection Failed",
            str(e)
        )
    except Exception as e: # pylint: disable=broad-except
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            f"Internal server error: {str(e)}"
        )


@control_app.route('/devices/<device_id>/connections', methods=['PUT'])
@authenticate_user
def update_connection(device_id: str):
    """Update cached ServiceMap for a device (NIPC Section 4.4.2)."""
    device = session.get(BleExtension, device_id)
    if device is None:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_ID,
            HTTPStatus.NOT_FOUND,
            "Not Found",
            f"Device ID {device_id} does not exist or is not a device"
        )

    # Check if device is connected
    conn = ble_ap().get_connection(device.device_mac_address)
    if not conn:
        return create_nipc_problem_response(
            NipcProblemTypes.PROTOCOLMAP_BLE_NO_CONNECTION,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            f"No connection found for device {device_id}"
        )

    # Default service discovery parameters
    services = []
    cached = False
    cache_idle_purge = 3600
    auto_update = True

    # Parse request body if provided
    if request.is_json and request.json:
        protocol_map = request.json.get("sdfProtocolMap", {})
        ble_config = protocol_map.get("ble", {})
        if ble_config:
            services = [
                {"serviceID": svc.get("serviceID")}
                for svc in ble_config.get("services", [])
            ]
            cached = bool(ble_config.get("cached", cached))
            cache_idle_purge = int(ble_config.get("cacheIdlePurge", cache_idle_purge))
            auto_update = bool(ble_config.get("autoUpdate", auto_update))

    try:
        connect_options = BleConnectOptions(services, cached, cache_idle_purge)
        discover_result = ble_ap().discover(
            device.device_mac_address,
            connect_options,
            0  # No retries for discovery on existing connection
        )

        response_data = {
            "id": device_id,
            "sdfProtocolMap": {
                "ble": [
                    {
                        "serviceID": svc.service_id,
                        "characteristics": [
                            {
                                "characteristicID": char.characteristic_id,
                                "flags": char.properties,
                                "descriptors": char.descriptors
                            }
                            for char in svc.characteristics.values()
                        ]
                    }
                    for svc in discover_result.services
                ]
            }
        }
        return jsonify(response_data), HTTPStatus.OK
    except BleDiscoveryError as e:
        return create_nipc_problem_response(
            NipcProblemTypes.PROTOCOLMAP_BLE_NO_CONNECTION,
            HTTPStatus.BAD_REQUEST,
            "Discovery Failed",
            str(e)
        )
    except Exception as e: # pylint: disable=broad-except
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            f"Internal server error: {str(e)}"
        )


@control_app.route('/devices/<device_id>/connections', methods=['DELETE'])
@authenticate_user
def disconnect_from_device(device_id: str):
    """Disconnect from a device (NIPC Section 4.4.3)."""
    device = session.get(BleExtension, device_id)
    if device is None:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_ID,
            HTTPStatus.NOT_FOUND,
            "Not Found",
            f"Device ID {device_id} does not exist or is not a device"
        )

    try:
        ble_ap().disconnect(device.device_mac_address)
        return jsonify({"id": device_id}), HTTPStatus.OK
    except BleDisconnectError as e:
        return create_nipc_problem_response(
            NipcProblemTypes.PROTOCOLMAP_BLE_NO_CONNECTION,
            HTTPStatus.BAD_REQUEST,
            "Disconnect Failed",
            str(e)
        )
    except Exception as e: # pylint: disable=broad-except
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            f"Internal server error: {str(e)}"
        )


@control_app.route('/devices/<device_id>/connections', methods=['GET'])
@authenticate_user
def get_connection_status(device_id: str):
    """Get connection status for a device (NIPC Section 4.4.4)."""
    device = session.get(BleExtension, device_id)
    if device is None:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_ID,
            HTTPStatus.NOT_FOUND,
            "Not Found",
            f"Device ID {device_id} does not exist or is not a device"
        )

    try:
        conn = ble_ap().get_connection(device.device_mac_address)

        if conn:
            response_data = {
                "id": device_id,
                "sdfProtocolMap": {
                    "ble": [
                        {
                            "serviceID": svc.service_id,
                            "characteristics": [
                                {
                                    "characteristicID": char.characteristic_id,
                                    "flags": char.properties,
                                    "descriptors": char.descriptors
                                }
                                for char in svc.characteristics.values()
                            ]
                        }
                        for svc in conn.services.values()
                    ]
                }
            }
            return jsonify(response_data), HTTPStatus.OK

        return create_nipc_problem_response(
            NipcProblemTypes.PROTOCOLMAP_BLE_NO_CONNECTION,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            f"No connection found for device {device_id}"
        )
    except Exception as e: # pylint: disable=broad-except
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            f"Internal server error: {str(e)}"
        )

def parse_sdf_reference(sdf_reference: str) -> tuple[str, list[str]]:
    """Parse an SDF reference into namespace and path components.
    
    Args:
        sdf_reference: SDF reference like
            "https://example.com/thermometer#/sdfThing/thermometer/sdfProperty/temperature"

    Returns:
        tuple of (namespace, path_components)
    """
    try:
        # Split on '#' to separate namespace from path
        if '#' not in sdf_reference:
            raise ValueError("Invalid SDF reference: missing '#'")

        namespace, json_pointer = sdf_reference.split('#', 1)

        # Parse JSON pointer path (remove leading '/')
        if not json_pointer.startswith('/'):
            raise ValueError("Invalid SDF reference: JSON pointer must start with '/'")

        path_components = json_pointer[1:].split('/') if len(json_pointer) > 1 else []
        return namespace, path_components
    except Exception as e: # pylint: disable=broad-except
        raise ValueError(f"Failed to parse SDF reference '{sdf_reference}': {str(e)}") from e

def lookup_sdf_model(namespace: str) -> dict:
    """Look up an SDF model by namespace.
    
    Args:
        namespace: The namespace URL for the SDF model
    
    Returns:
        The SDF model dictionary
    
    Raises:
        ValueError: If model not found
    """
    # First try exact match by sdf_name
    model = session.scalar(select(SdfModel).filter_by(sdf_name=namespace))
    if model:
        return model.model

    # If not found, try to match by namespace in the model itself
    models = session.execute(select(SdfModel)).scalars().all()
    for model in models:
        model_dict = model.model
        if 'namespace' in model_dict:
            # Check if any namespace value matches
            namespaces = model_dict['namespace']
            if isinstance(namespaces, dict):
                for _, ns_url in namespaces.items():
                    if ns_url == namespace:
                        return model_dict
            elif isinstance(namespaces, str) and namespaces == namespace:
                return model_dict

    raise ValueError(f"SDF model not found for namespace '{namespace}'")

def navigate_sdf_model(model: dict, path_components: list[str]) -> dict:
    """Navigate to a specific property in an SDF model.
    
    Args:
        model: The SDF model dictionary
        path_components: List of path components like
            ['sdfThing', 'thermometer', 'sdfProperty', 'temperature']

    Returns:
        The property definition dictionary
    
    Raises:
        ValueError: If path is invalid or property not found
    """
    current = model
    path_str = '/'.join(path_components)

    try:
        for component in path_components:
            if not isinstance(current, dict) or component not in current:
                raise KeyError(f"Component '{component}' not found")
            current = current[component]

        return current
    except (KeyError, TypeError) as e:
        raise ValueError(f"Invalid SDF path '{path_str}': {str(e)}") from e

def extract_protocol_map(property_def: dict, protocol: str = 'ble') -> dict:
    """Extract protocol mapping from a property definition.
    
    Args:
        property_def: The property definition from SDF model
        protocol: Protocol name (default: 'ble')
    
    Returns:
        Protocol mapping dictionary
    
    Raises:
        ValueError: If protocol mapping not found
    """
    if 'sdfProtocolMap' not in property_def:
        raise ValueError("Property does not have protocol mapping")

    protocol_map = property_def['sdfProtocolMap']
    if protocol not in protocol_map:
        raise ValueError(f"Protocol '{protocol}' not found in protocol mapping")

    return protocol_map[protocol]


@control_app.route('/devices/<device_id>/properties', methods=['GET'])
@authenticate_user
def read_properties(device_id: str):
    """Read property values from a device (NIPC Section 4.1.2)."""
    try:
        # Get property names from query parameter
        property_names = request.args.getlist('propertyName')
        if not property_names:
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_SDF_URL,
                HTTPStatus.BAD_REQUEST,
                "Missing Property Name",
                "Query parameter 'propertyName' is required"
            )

        # Look up device
        device = session.get(BleExtension, device_id)
        if device is None:
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_ID,
                HTTPStatus.NOT_FOUND,
                "Device Not Found",
                f"Device ID {device_id} does not exist or is not a device"
            )

        results = []
        services = []

        for property_name in property_names:
            try:
                # URL decode the property name
                property_name = urllib.parse.unquote(property_name)

                # Parse SDF reference
                namespace, path_components = parse_sdf_reference(property_name)

                # Look up SDF model
                model = lookup_sdf_model(namespace)

                # Navigate to property
                property_def = navigate_sdf_model(model, path_components)

                # Extract BLE protocol mapping
                ble_mapping = extract_protocol_map(property_def, 'ble')

                # Perform BLE read
                service_id = ble_mapping['serviceID'].lower()
                characteristic_id = ble_mapping['characteristicID'].lower()

                services.append((property_name, service_id, characteristic_id))
            except Exception as e: # pylint: disable=broad-except
                results.append({
                    "type": NipcProblemTypes.INVALID_SDF_URL,
                    "status": HTTPStatus.BAD_REQUEST.value,
                    "title": "Invalid SDF Reference",
                    "detail": str(e)
                })

        # if device is not connected, connect first
        implicit_connect = False
        if device.device_mac_address not in ble_ap().conn_reqs:
            implicit_connect = True
            ble_ap().connect(device.device_mac_address, BleConnectOptions())
            ble_ap().discover(device.device_mac_address, BleConnectOptions(
                services=[service_id for _, service_id, _ in services]
            ))

        for property_name, service_id, characteristic_id in services:
            try:
                resp = ble_ap().read(
                    device.device_mac_address, service_id, characteristic_id)

                results.append({
                    "property": property_name,
                    "value": base64.b64encode(resp.value).decode('utf-8')
                })
            except BleReadError as e:
                results.append({
                    "type": NipcProblemTypes.PROPERTY_NOT_READABLE,
                    "status": HTTPStatus.INTERNAL_SERVER_ERROR.value,
                    "title": "Property Read Error",
                    "detail": f"Failed to read property {property_name}: {str(e)}"
                })

        if implicit_connect:
            ble_ap().disconnect(device.device_mac_address)

        return jsonify(results), HTTPStatus.OK
    except Exception as e: # pylint: disable=broad-except
        return create_nipc_problem_response(
            NipcProblemTypes.PROPERTY_NOT_READABLE,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            f"Unexpected error: {str(e)}"
        )


@control_app.route('/devices/<device_id>/properties', methods=['PUT'])
@authenticate_user
def write_properties(device_id: str):
    """Write property values to a device (NIPC Section 4.1.1)."""
    try:
        # Validate request body
        try:
            request_json = request.json
        except Exception: # pylint: disable=broad-except
            # Handle case where request.json raises an exception (e.g., no Content-Type)
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_SDF_URL,
                HTTPStatus.BAD_REQUEST,
                "Missing Request Body",
                "Request body with property array is required"
            )

        if not request_json:
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_SDF_URL,
                HTTPStatus.BAD_REQUEST,
                "Missing Request Body",
                "Request body with property array is required"
            )

        properties_to_write = request_json
        if not isinstance(properties_to_write, list):
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_SDF_URL,
                HTTPStatus.BAD_REQUEST,
                "Invalid Request Format",
                "Request body must be an array of property objects"
            )

        # Look up device
        device = session.get(BleExtension, device_id)
        if device is None:
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_ID,
                HTTPStatus.NOT_FOUND,
                "Device Not Found",
                f"Device ID {device_id} does not exist or is not a device"
            )

        results = []
        services = []

        for prop_obj in properties_to_write:
            try:
                property_name = prop_obj['property']
                value = prop_obj['value']

                # Parse SDF reference
                namespace, path_components = parse_sdf_reference(property_name)

                # Look up SDF model
                model = lookup_sdf_model(namespace)

                # Navigate to property
                property_def = navigate_sdf_model(model, path_components)

                # Extract BLE protocol mapping
                ble_mapping = extract_protocol_map(property_def, 'ble')

                # Add service to list
                services.append((property_name,
                                ble_mapping['serviceID'].lower(),
                                ble_mapping['characteristicID'].lower(),
                                value))
            except Exception as e: # pylint: disable=broad-except
                results.append({
                    "type": NipcProblemTypes.INVALID_SDF_URL,
                    "status": HTTPStatus.BAD_REQUEST.value,
                    "title": "Invalid SDF Reference",
                    "detail": str(e)
                })

        # if device is not connected, connect first
        implicit_connect = False
        if device.device_mac_address not in ble_ap().conn_reqs:
            implicit_connect = True
            ble_ap().connect(device.device_mac_address, BleConnectOptions())
            ble_ap().discover(device.device_mac_address, BleConnectOptions(
                services=[service_id for _, service_id, _, _ in services]
            ))

        for property_name, service_id, characteristic_id, value in services:
            try:
                # Parse SDF reference
                namespace, path_components = parse_sdf_reference(property_name)

                # Look up SDF model
                model = lookup_sdf_model(namespace)

                # Navigate to property
                property_def = navigate_sdf_model(model, path_components)

                # Check if property is writable
                if property_def.get('writable', True) is False:
                    results.append({
                        "type": NipcProblemTypes.PROPERTY_NOT_WRITABLE,
                        "status": HTTPStatus.BAD_REQUEST.value,
                        "title": "Property Not Writable",
                        "detail": f"Property {property_name} is not writable"
                    })
                    continue

                # Extract BLE protocol mapping
                ble_mapping = extract_protocol_map(property_def, 'ble')

                # Assume it's base64 encoded
                binary_data = base64.b64decode(value)

                # Perform BLE write
                service_id = ble_mapping['serviceID'].lower()
                characteristic_id = ble_mapping['characteristicID'].lower()

                ble_ap().write(
                    device.device_mac_address, service_id, characteristic_id, binary_data)

                results.append({
                    "status": HTTPStatus.OK.value
                })
            except BleWriteError as e:
                results.append({
                    "type": NipcProblemTypes.PROPERTY_NOT_WRITABLE,
                    "status": HTTPStatus.INTERNAL_SERVER_ERROR.value,
                    "title": "Property Write Error",
                    "detail": f"Failed to write property {property_name}: {str(e)}"
                })

        if implicit_connect:
            ble_ap().disconnect(device.device_mac_address)

        return jsonify(results), HTTPStatus.OK
    except Exception as e: # pylint: disable=broad-except
        return create_nipc_problem_response(
            NipcProblemTypes.PROPERTY_NOT_WRITABLE,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            f"Unexpected error: {str(e)}"
        )

@control_app.route('/registrations/models', methods=['POST'])
@authenticate_user
def register_sdf_model():
    """Register an SDF model (NIPC draft-06 section 3.1.1)."""
    if not request.is_json:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Request body must be JSON"
        )
    try:
        sdf_model = request.get_json()
        namespace = sdf_model.get("namespace")
        default_namespace = sdf_model.get("defaultNamespace")
        if not namespace or not default_namespace:
            raise SchemaError(
                "Missing namespace or defaultNamespace in SDF model")
        sdf_name = namespace[default_namespace]
        if "sdfThing" in sdf_model and sdf_model["sdfThing"]:
            sdf_name += "#/" + next(iter(sdf_model["sdfThing"].keys()))
        elif "sdfObject" in sdf_model and sdf_model["sdfObject"]:
            sdf_name += "#/" + next(iter(sdf_model["sdfObject"].keys()))
        else:
            raise SchemaError("SDF model must have sdfThing or sdfObject")
        existing = session.scalar(
            select(SdfModel).filter_by(sdf_name=sdf_name))
        if existing:
            return create_nipc_problem_response(
                NipcProblemTypes.SDF_MODEL_ALREADY_REGISTERED,
                HTTPStatus.CONFLICT,
                "Conflict",
                "SDF model already registered"
            )
        model_obj = SdfModel(sdf_name=sdf_name, model=sdf_model)
        session.add(model_obj)
        session.commit()
        return jsonify([{"sdfName": sdf_name}]), HTTPStatus.OK
    except SchemaError as e:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            str(e)
        )
    except Exception as e: # pylint: disable=broad-except  # pylint: disable=broad-except
        logging.exception(
            "Unexpected error during SDF model registration %s", e)
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Internal server error"
        )


@control_app.route('/registrations/models', methods=['GET'])
@authenticate_user
def get_sdf_model():
    """Fetch a registered SDF model by sdfName (query parameter) or list all models."""
    sdf_name = request.args.get('sdfName')
    if sdf_name:
        # Get specific model
        sdf_name = urllib.parse.unquote(sdf_name)
        model = session.scalar(select(SdfModel).filter_by(sdf_name=sdf_name))
        if not model:
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_SDF_URL,
                HTTPStatus.NOT_FOUND,
                "Not Found",
                "SDF model not found"
            )
        return jsonify(model.model), HTTPStatus.OK

    # List all models
    models = session.execute(select(SdfModel)).scalars().all()
    return jsonify([m.serialize() for m in models]), HTTPStatus.OK


@control_app.route('/registrations/models', methods=['PUT'])
@authenticate_user
def update_sdf_model():
    """
    Update a registered SDF model by sdfName (query parameter). 
    Namespace and defaultNamespace cannot be changed.
    """
    sdf_name = request.args.get('sdfName')
    if not sdf_name:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Missing sdfName query parameter"
        )

    sdf_name = urllib.parse.unquote(sdf_name)
    if not request.is_json:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request", 
            "Request body must be JSON"
        )
    model = session.scalar(select(SdfModel).filter_by(sdf_name=sdf_name))
    if not model:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.NOT_FOUND,
            "Not Found",
            "SDF model not found"
        )
    try:
        sdf_model = request.get_json()
        # Disallow changing namespace or defaultNamespace
        orig = model.model
        if ("namespace" in sdf_model and sdf_model["namespace"] != orig.get("namespace")) or \
           ("defaultNamespace" in sdf_model and
                sdf_model["defaultNamespace"] != orig.get("defaultNamespace")):
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_SDF_URL,
                HTTPStatus.BAD_REQUEST,
                "Bad Request",
                "Cannot update namespace or defaultNamespace of an existing SDF model."
            )
        model.model = sdf_model
        session.commit()
        return jsonify({"sdfName": sdf_name}), HTTPStatus.OK
    except Exception as e: # pylint: disable=broad-except  # pylint: disable=broad-except
        logging.exception("Unexpected error during SDF model update %s", e)
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Internal server error"
        )


@control_app.route('/registrations/models', methods=['DELETE'])
@authenticate_user
def delete_sdf_model():
    """Delete a registered SDF model by sdfName (query parameter)."""
    sdf_name = request.args.get('sdfName')
    if not sdf_name:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Missing sdfName query parameter"
        )

    sdf_name = urllib.parse.unquote(sdf_name)
    model = session.scalar(select(SdfModel).filter_by(sdf_name=sdf_name))
    if not model:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.NOT_FOUND,
            "Not Found",
            "SDF model not found"
        )
    session.delete(model)
    session.commit()
    return jsonify({"sdfName": sdf_name}), HTTPStatus.OK

@control_app.route('/registrations/data-apps', methods=['POST'])
@authenticate_user
def register_data_app():
    """Register a data application (NIPC)."""
    if not request.is_json:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Request body must be JSON"
        )

    data_app_id = request.args.get('dataAppId')
    if not data_app_id:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Missing dataAppId query parameter"
        )

    try:
        body = request.get_json()

        events = body.get('events')

        for event in events:
            event_name = event.get('event')
            namespace, path_components = parse_sdf_reference(event_name)
            model = lookup_sdf_model(namespace)
            if not model:
                return create_nipc_problem_response(
                    NipcProblemTypes.INVALID_SDF_URL,
                    HTTPStatus.BAD_REQUEST,
                    "Bad Request",
                    "Request body must contain a list of events"
                )
            navigate_sdf_model(model, path_components)

        mqtt_client = body.get('mqttClient')
        if mqtt_client is not True:
            return create_nipc_problem_response(
                NipcProblemTypes.ABOUT_BLANK,
                HTTPStatus.BAD_REQUEST,
                "Bad Request",
                "mqttClient must be true"
            )

        data_app = DataApp(data_app_id, [ev["event"] for ev in events])
        session.add(data_app)
        session.commit()
        return jsonify(body), HTTPStatus.OK
    except Exception as e: # pylint: disable=broad-except
        logging.exception("Unexpected error during data app registration %s", e)
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Internal server error"
        )


@control_app.route('/registrations/data-apps', methods=['GET'])
@authenticate_user
def get_data_app():
    """Get a data application (NIPC) by ID."""
    data_app_id = request.args.get('dataAppId')
    if not data_app_id:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Missing dataAppId query parameter"
        )

    try:
        data_app = session.query(DataApp).filter_by(data_app_id=data_app_id).first()
        if not data_app:
            return create_nipc_problem_response(
                NipcProblemTypes.ABOUT_BLANK,
                HTTPStatus.NOT_FOUND,
                "Not Found",
                f"Data app with ID {data_app_id} not found"
            )

        response_body = {
            "events": [{"event": event} for event in data_app.events],
            "mqttClient": True
        }
        return jsonify(response_body), HTTPStatus.OK
    except Exception as e: # pylint: disable=broad-except
        logging.exception("Unexpected error during data app retrieval %s", e)
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Internal server error"
        )


@control_app.route('/registrations/data-apps', methods=['PUT'])
@authenticate_user
def update_data_app():
    """Update a data application (NIPC)."""
    if not request.is_json:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Request body must be JSON"
        )

    data_app_id = request.args.get('dataAppId')
    if not data_app_id:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Missing dataAppId query parameter"
        )

    try:
        data_app = session.query(DataApp).filter_by(data_app_id=data_app_id).first()
        if not data_app:
            return create_nipc_problem_response(
                NipcProblemTypes.ABOUT_BLANK,
                HTTPStatus.NOT_FOUND,
                "Not Found",
                f"Data app with ID {data_app_id} not found"
            )

        body = request.get_json()
        events = body.get('events')

        for event in events:
            event_name = event.get('event')
            namespace, path_components = parse_sdf_reference(event_name)
            model = lookup_sdf_model(namespace)
            if not model:
                return create_nipc_problem_response(
                    NipcProblemTypes.INVALID_SDF_URL,
                    HTTPStatus.BAD_REQUEST,
                    "Bad Request",
                    "Request body must contain a list of events"
                )
            navigate_sdf_model(model, path_components)

        mqtt_client = body.get('mqttClient')
        if mqtt_client is not True:
            return create_nipc_problem_response(
                NipcProblemTypes.ABOUT_BLANK,
                HTTPStatus.BAD_REQUEST,
                "Bad Request",
                "mqttClient must be true"
            )

        # Update the data app events
        data_app.events = [ev["event"] for ev in events]
        session.commit()
        return jsonify(body), HTTPStatus.OK
    except Exception as e: # pylint: disable=broad-except
        logging.exception("Unexpected error during data app update %s", e)
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Internal server error"
        )


@control_app.route('/registrations/data-apps', methods=['DELETE'])
@authenticate_user
def delete_data_app():
    """Delete a data application (NIPC) by ID."""
    data_app_id = request.args.get('dataAppId')
    if not data_app_id:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_SDF_URL,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Missing dataAppId query parameter"
        )

    try:
        data_app = session.query(DataApp).filter_by(data_app_id=data_app_id).first()
        if not data_app:
            return create_nipc_problem_response(
                NipcProblemTypes.ABOUT_BLANK,
                HTTPStatus.NOT_FOUND,
                "Not Found",
                f"Data app with ID {data_app_id} not found"
            )

        # Build response body before deletion
        response_body = {
            "events": [{"event": event} for event in data_app.events],
            "mqttClient": True
        }

        session.delete(data_app)
        session.commit()
        return jsonify(response_body), HTTPStatus.OK
    except Exception as e: # pylint: disable=broad-except
        logging.exception("Unexpected error during data app deletion %s", e)
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Internal server error"
        )

@control_app.route('/devices/<device_id>/events', methods=["POST"])
@authenticate_user
def enable_event(device_id: str):
    """Enable an event for a device."""
    # check if device exists
    device = session.query(Device).filter_by(device_id=device_id).first()
    if not device:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_ID,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            f"Device with ID {device_id} not found"
        )

    try:
        event_name = request.args.get('eventName')
        if not event_name:
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_SDF_URL,
                HTTPStatus.BAD_REQUEST,
                "Bad Request",
                "Missing eventName query parameter"
            )

        namespace, path_components = parse_sdf_reference(event_name)
        model = lookup_sdf_model(namespace)
        if not model:
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_SDF_URL,
                HTTPStatus.BAD_REQUEST,
                "Bad Request",
                "Request body must contain a list of events"
            )
        protocol_map = navigate_sdf_model(model, path_components)

        if not protocol_map:
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_SDF_URL,
                HTTPStatus.BAD_REQUEST,
                "Bad Request",
                "Request body must contain a list of events"
            )

        # check if event already exists
        event = session.query(Event).filter_by(event_name=event_name, device_id=device_id).first()
        if event:
            return create_nipc_problem_response(
                NipcProblemTypes.EVENT_ALREADY_ENABLED,
                HTTPStatus.BAD_REQUEST,
                "Bad Request",
                "Event already exists"
            )

        # protocol_map["sdfOutputData"]["sdfProtocolMap"]["ble"]["type"] is the event_type
        event_type = protocol_map["sdfOutputData"]["sdfProtocolMap"]["ble"]["type"]
        gatt_service_id = None
        gatt_char_id = None
        if event_type == "gatt":
            gatt_service_id = protocol_map["sdfOutputData"]["sdfProtocolMap"]["ble"]["serviceID"]
            gatt_char_id = (
                protocol_map["sdfOutputData"]["sdfProtocolMap"]["ble"]["characteristicID"]
            )

        instance_id = uuid.uuid4()
        # create event
        event = Event(
            event_name=event_name,
            instance_id=instance_id,
            device_id=device_id,
            event_type=event_type,
            gatt_service_id=gatt_service_id,
            gatt_characteristic_id=gatt_char_id
        )
        session.add(event)
        session.commit()
        base_path = request.base_url
        return "", HTTPStatus.CREATED, {"Location": f"{base_path}?instanceId={instance_id}"}
    except Exception as e: # pylint: disable=broad-except
        logging.exception("Unexpected error during event lookup %s", e)
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Internal server error"
        )

@control_app.route('/devices/<device_id>/events', methods=["DELETE"])
@authenticate_user
def disable_event(device_id: str):
    """Disable an event for a device."""
    instance_id = request.args.get('instanceId')
    if not instance_id:
        return create_nipc_problem_response(
            NipcProblemTypes.INVALID_ID,
            HTTPStatus.BAD_REQUEST,
            "Bad Request",
            "Missing instanceId query parameter"
        )
    try:
        event = session.query(Event).filter_by(device_id=device_id, instance_id=instance_id).first()
        if not event:
            return create_nipc_problem_response(
                NipcProblemTypes.INVALID_ID,
                HTTPStatus.BAD_REQUEST,
                "Bad Request",
                f"Event for device ID {device_id} not found"
            )
        session.delete(event)
        session.commit()
        return "", HTTPStatus.NO_CONTENT
    except Exception as e: # pylint: disable=broad-except
        logging.exception("Unexpected error during event disable %s", e)
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Internal server error"
        )

@control_app.route('/devices/<device_id>/events', methods=["GET"])
@authenticate_user
def get_events(device_id: str):
    """Get events for a device."""
    try:
        instance_ids = request.args.getlist('instanceId')
        if not instance_ids:
            # return all events for the device
            events = session.query(Event).filter_by(device_id=device_id).all()
            return jsonify([
                {"event": event.event_name, "instanceId": event.instance_id}
                for event in events
            ]), HTTPStatus.OK
        events = []
        for instance_id in instance_ids:
            event = session.query(Event).filter_by(
                device_id=device_id,
                instance_id=instance_id
            ).first()
            if not event:
                return create_nipc_problem_response(
                    NipcProblemTypes.INVALID_ID,
                    HTTPStatus.BAD_REQUEST,
                    "Bad Request",
                    f"Event for device ID {device_id} not found"
                )
            events.append({"event": event.event_name, "instanceId": event.instance_id})
        return jsonify(events), HTTPStatus.OK
    except Exception as e: # pylint: disable=broad-except
        logging.exception("Unexpected error during event lookup %s", e)
        return create_nipc_problem_response(
            NipcProblemTypes.ABOUT_BLANK,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "Internal server error"
        )
