#!/bin/bash

echo '*.* @central-logging:5514' >> /etc/rsyslog.conf
service rsyslog restart
