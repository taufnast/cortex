import json
from pathlib import Path


ERROR_PREFIX = "Error:"


class PoseParser:
    tag = 'pose'

    def parse(self, context, data):
        """
        parse data according to the cortex.proto file

        :param context: context object that includes common functions such as save
        :param data: serialized json data or a dictionary
        :return: parsed data as dict
        """
        if isinstance(data, dict):
            snapshot = data
        else:
            snapshot = json.loads(data)

        if self.tag not in snapshot.keys():
            print(f'{ERROR_PREFIX} couldn\'t find {self.tag} in supplied data.')
            # no data to parse
            return {}

        expected_attr = ["translation", "rotation"]
        if len(snapshot[self.tag].keys()) != len(expected_attr):
            print(f'{ERROR_PREFIX} snapshot has a wrong format. Expected - {expected_attr}')
            # no data to parse
            return {}

        parsed_pose = {}
        for attr in expected_attr:
            if attr not in snapshot[self.tag].keys():
                print(f'{ERROR_PREFIX} snapshot has no {attr}.')
                # no data to parse
                return {}
            parsed_pose[attr] = snapshot[self.tag][attr]

        if "snapshot_path" in snapshot:
            sp = snapshot["snapshot_path"]
        else:
            sp = "/tmp/pose"
            Path(sp).mkdir(parents=True, exist_ok=True)

        datetmp = None
        if "datetime" in snapshot:
            datetime = snapshot["datetime"]
        return {
            "snapshot_path": sp,
            "timestamp": datetime,
            "parser": self.tag,
            "result": parsed_pose,
        }
