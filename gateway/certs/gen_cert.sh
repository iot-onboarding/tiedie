#!/bin/bash

name=$1

openssl req -nodes -new -keyout $name.key -out $name.csr -subj "/C=US/ST=CA/L=San Jose/O=My Company/OU=My Department/CN=$name"
openssl x509 -req -days 365 -in $name.csr -CA ../ca_certificates/ca.pem -CAkey ../ca_certificates/ca.key -CAcreateserial -out $name.crt                              
openssl pkcs12 -export -out $name.p12 -inkey $name.key -in $name.crt        

rm $name.csr
rm $name.key
rm $name.crt
