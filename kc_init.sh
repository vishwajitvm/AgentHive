#!/bin/sh
/opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080/ --realm master --user admin --password admin
/opt/keycloak/bin/kcadm.sh create realms -s realm=agenthive -s enabled=true
/opt/keycloak/bin/kcadm.sh create clients -r agenthive -s clientId=agenthive-frontend -s enabled=true -s publicClient=true -s 'redirectUris=["http://localhost:3000/*"]' -s 'webOrigins=["http://localhost:3000"]'
/opt/keycloak/bin/kcadm.sh create users -r agenthive -s username=vishwajit -s enabled=true -s emailVerified=true -s firstName=Vishwajit -s lastName=VM -s email=vishwajit@example.com
/opt/keycloak/bin/kcadm.sh set-password -r agenthive --username vishwajit --new-password password123
