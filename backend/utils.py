import logging

from datetime import timedelta
from functools import update_wrapper

from flask import make_response, request, current_app
from flask import Response


logger = logging.getLogger("savvy.utils")


def json_error(msg, status_code=200, **data):
    import json
    import pprint
    try:
        request_dump = pprint.pformat(vars(request))
        if len(request_dump) > 4096:
            request_dump = "{}<truncated to 4096 bytes>".format(request_dump[:4096])
        logger.debug(request_dump)
    except Exception as e:
        logger.error("Unable to log request dump: {}".format(e))

    if isinstance(msg, Exception):
        msg = str(msg)
    response_data = {"error": msg}
    response_data.update(data)
    response = Response(json.dumps(response_data), mimetype="application/json")
    response.status_code = status_code
    return response


def json_success(msg, status_code=200, **data):
    import json
    response_data = {"success": msg}
    response_data.update(data)
    logger.debug("JSON Success Msg: {}".format(response_data))
    response = Response(json.dumps(response_data), mimetype="application/json")
    response.status_code = status_code
    return response


def hash_password(passwd, salt=None):
    """Creates a hash from a password using a salt and 100 rounds of SHA512."""
    import hashlib
    import os

    salt = salt or os.urandom(512)
    passwd = bytes(passwd, "utf-8")
    hashed_password = hashlib.sha512(passwd + salt).digest()
    for _ in range(100):
        hashed_password = hashlib.sha512(passwd + salt + hashed_password).digest()
    return hashed_password, salt


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, (str, bytes)):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, (str, bytes)):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def get_google_places_by_id(place_id):
    import requests
    url = "https://maps.googleapis.com/maps/api/place/details/json?key=AIzaSyD2NjLAT9oyFc2RxlYy0P30ejMXvAaUdV4&placeid={}".format(place_id)
    response = requests.get(url)
    data = response.json()
    if data["status"] != "OK":
        raise Exception("Invalid Google Places ID or Google API error.")
    return data["result"]

