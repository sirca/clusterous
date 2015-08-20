#!/bin/bash

echo '*.* @central_logging:5514' >> /etc/rsyslog.conf
service rsyslog restart
