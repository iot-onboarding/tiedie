#!/bin/bash

name=$1

openssl req -nodes -new -keyout $name.key -out $name.csr -subj "/C=US/O=TieDie Test Cert/OU=Test.$$/CN=$name"
openssl x509 -req -days 365 -in $name.csr -CA ../ca_certificates/ca.pem -CAkey ../ca_certificates/ca.key -CAcreateserial -out $name.crt                              
openssl pkcs12 -export -out $name.p12 -inkey $name.key -in $name.crt        

rm $name.csr
