#!/bin/sh
/opt/keycloak/bin/kcadm.sh create clients -r agenthive -s clientId=agenthive-frontend -s enabled=true -s publicClient=true -s 'redirectUris=["http://localhost:3000/*"]' -s 'webOrigins=["http://localhost:3000"]'
