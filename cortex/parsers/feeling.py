import json


ERROR_PREFIX = "Error:"


def parse_feelings(context, snapshot):
    if not isinstance(snapshot, dict):
        snapshot = json.loads(snapshot)

    expected_attr = ["hunger", "thirst", "exhaustion", "happiness"]
    if parse_feelings.tag not in snapshot.keys():
        print(f'{ERROR_PREFIX} couldn\'t find {parse_feelings.tag} in supplied data.')
        # no data to parse
        return {}

    parsed_feelings = {}

    for attr in expected_attr:
        if attr not in snapshot[parse_feelings.tag].keys():
            print(f'{ERROR_PREFIX} snapshot has no {attr}.')
            # no data to parse
            return {}
        parsed_feelings[attr] = snapshot[parse_feelings.tag][attr]

    if "snapshot_path" in snapshot:
        sp = snapshot["snapshot_path"]
    else:
        sp = "/tmp/pose"

    datetmp = None
    if "datetime" in snapshot:
        datetime = snapshot["datetime"]
    return {
        "snapshot_path": sp,
        "timestamp": datetime,
        "parser": parse_feelings.tag,
        "result": parsed_feelings,
    }


parse_feelings.tag = 'feelings'
