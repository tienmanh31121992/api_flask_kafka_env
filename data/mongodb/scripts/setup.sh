#!/bin/bash

echo "Waiting for startup.."
until curl http://mongodb:27017/serverStatus\?text\=1 2>&1 | grep uptime | head -1; do
  printf '.'
  sleep 1
done

echo curl http://mongodb:27017/serverStatus\?text\=1 2>&1 | grep uptime | head -1
echo "Started.."

echo SETUP.sh time now: $(date +"%T")

mongod --bind_ip_all --replSet rs0
mongo --host mongodb:27017 <<EOF
   var cfg = {
        "_id": "rs0",
        "members": [
            {
                "_id": 0,
                "host": "mongodb:27017"
            }
        ]
    };
    rs.initiate(cfg, { force: true });
    rs.reconfig(cfg, { force: true });
EOF
