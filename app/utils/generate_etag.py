import hashlib
import json


def generate_etag(data):
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_data.encode("utf-8")).hexdigest()
