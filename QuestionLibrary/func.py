import requests


class TokenExpired(Exception):
    pass


def formattedFieldName(layer_id, field_name):
    return f"layer_{layer_id}_{field_name}"


def get_all_features(url, token, where="1=1"):
    offset = 0
    limit = 100
    r = None
    f = []
    while True:
        data = {"token": token, "f": "json", "where": where, "outFields": "*",
                "resultRecordCount": limit, "resultOffset": offset, "exceedTransferLimit": True}
        response = requests.post(f"{url}/query", data=data)

        response_json = response.json()

        if r is None:
            r = response_json

        if "error" in response_json:
            if response_json["error"]["code"] == 498:
                raise TokenExpired(response.content)

            raise Exception(response.content)

        if len(response_json["features"]) > 0:
            f += response_json["features"]
            offset += limit
        else:
            break
        r['features'] = f
    return r
