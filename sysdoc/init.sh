#!/bin/bash
export PYTHONPATH='/home/fcmapp/.local/lib/python3.6/site-packages'
/home/fcmapp/.local/bin/gunicorn -b 0.0.0.0:$1 --pythonpath='/home/fcmapp/.local/lib/python3.6/site-packages' --certfile fullchain.pem --keyfile privkey.pem --timeout 5000 --reload -w 4 wsgi
