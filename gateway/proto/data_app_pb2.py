# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: data_app.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x64\x61ta_app.proto\x12\x06tiedie\"\xc6\x07\n\x10\x44\x61taSubscription\x12\x16\n\tdevice_id\x18\x01 \x01(\tH\x01\x88\x01\x01\x12\x0c\n\x04\x64\x61ta\x18\x02 \x01(\x0c\x12\x44\n\x10\x62le_subscription\x18\x03 \x01(\x0b\x32(.tiedie.DataSubscription.BLESubscriptionH\x00\x12\x46\n\x11\x62le_advertisement\x18\x04 \x01(\x0b\x32).tiedie.DataSubscription.BLEAdvertisementH\x00\x12=\n\x06zigbee\x18\x05 \x01(\x0b\x32+.tiedie.DataSubscription.ZigbeeSubscriptionH\x00\x12:\n\x0braw_payload\x18\x06 \x01(\x0b\x32#.tiedie.DataSubscription.RawPayloadH\x00\x12M\n\x15\x62le_connection_status\x18\x07 \x01(\x0b\x32,.tiedie.DataSubscription.BLEConnectionStatusH\x00\x1aw\n\x0f\x42LESubscription\x12\x19\n\x0cservice_uuid\x18\x01 \x01(\tH\x00\x88\x01\x01\x12 \n\x13\x63haracteristic_uuid\x18\x02 \x01(\tH\x01\x88\x01\x01\x42\x0f\n\r_service_uuidB\x16\n\x14_characteristic_uuid\x1a\x43\n\x10\x42LEAdvertisement\x12\x13\n\x0bmac_address\x18\x01 \x01(\t\x12\x11\n\x04rssi\x18\x02 \x01(\x05H\x00\x88\x01\x01\x42\x07\n\x05_rssi\x1a\xc2\x01\n\x12ZigbeeSubscription\x12\x18\n\x0b\x65ndpoint_id\x18\x01 \x01(\x05H\x00\x88\x01\x01\x12\x17\n\ncluster_id\x18\x02 \x01(\x05H\x01\x88\x01\x01\x12\x19\n\x0c\x61ttribute_id\x18\x03 \x01(\x05H\x02\x88\x01\x01\x12\x1b\n\x0e\x61ttribute_type\x18\x04 \x01(\x05H\x03\x88\x01\x01\x42\x0e\n\x0c_endpoint_idB\r\n\x0b_cluster_idB\x0f\n\r_attribute_idB\x11\n\x0f_attribute_type\x1a]\n\x13\x42LEConnectionStatus\x12\x13\n\x0bmac_address\x18\x01 \x01(\t\x12\x11\n\tconnected\x18\x02 \x01(\x08\x12\x13\n\x06reason\x18\x03 \x01(\x05H\x00\x88\x01\x01\x42\t\n\x07_reason\x1a\x34\n\nRawPayload\x12\x17\n\ncontext_id\x18\x01 \x01(\tH\x00\x88\x01\x01\x42\r\n\x0b_context_idB\x0e\n\x0csubscriptionB\x0c\n\n_device_idB\x1a\n\x16\x63om.cisco.tiedie.protoP\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data_app_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\026com.cisco.tiedie.protoP\001'
  _globals['_DATASUBSCRIPTION']._serialized_start=27
  _globals['_DATASUBSCRIPTION']._serialized_end=993
  _globals['_DATASUBSCRIPTION_BLESUBSCRIPTION']._serialized_start=429
  _globals['_DATASUBSCRIPTION_BLESUBSCRIPTION']._serialized_end=548
  _globals['_DATASUBSCRIPTION_BLEADVERTISEMENT']._serialized_start=550
  _globals['_DATASUBSCRIPTION_BLEADVERTISEMENT']._serialized_end=617
  _globals['_DATASUBSCRIPTION_ZIGBEESUBSCRIPTION']._serialized_start=620
  _globals['_DATASUBSCRIPTION_ZIGBEESUBSCRIPTION']._serialized_end=814
  _globals['_DATASUBSCRIPTION_BLECONNECTIONSTATUS']._serialized_start=816
  _globals['_DATASUBSCRIPTION_BLECONNECTIONSTATUS']._serialized_end=909
  _globals['_DATASUBSCRIPTION_RAWPAYLOAD']._serialized_start=911
  _globals['_DATASUBSCRIPTION_RAWPAYLOAD']._serialized_end=963
# @@protoc_insertion_point(module_scope)