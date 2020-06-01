import numpy as np
import yaml
import json
import copy
from flask import Flask
from flask import request
from pika import BasicProperties
from cortex.msgbrokers import find_msg_broker
from cortex.reader import parse_from
from google.protobuf.json_format import MessageToDict, MessageToJson, ParseDict
from pathlib import Path
from secrets import token_hex


def get_parsers():
    """
    load yaml configuration of parsers

    :return: parsers configuration as a dict
    """
    with open('config/parsers.yaml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        # print(data)
        if "parsers" in data:
            return data["parsers"]
    return {}


def save_data(parsers, snapshot):
    """
    save data is looking for 'data' field (as it stores the 'big data', based on the cortex.proto)

    :param parsers: parsers as a dict (as return value of get_parsers())
    :param snapshot: as protobuf object
    :return: paths dict {parser_name : path__where_data_is_stored}
    """
    parser_paths = {}
    # parsers as appear in the parsers.yaml file should include path option
    # which will be used for saving big data
    for parser, config in parsers.items():
        if config is not None and "path" in config:
            parser_dir = Path(config["path"])
            parser_dir.mkdir(parents=True, exist_ok=True)
            parser_paths[parser] = parser_dir

    for desc, val in snapshot.ListFields():
        if desc.name in parser_paths:
            if desc.name == "color_image":  # save bytes object
                parser_paths[desc.name] = parser_paths[desc.name] / ("data_" + token_hex(5) + ".snap")
                with open(parser_paths[desc.name], "wb") as f:
                    f.write(snapshot.color_image.data)
            elif desc.name == "depth_image":  # save numpy array
                parser_paths[desc.name] = parser_paths[desc.name] / ("data_" + token_hex(5) + ".npy")
                np.save(parser_paths[desc.name], snapshot.depth_image.data)
    return parser_paths


def snapshot_to_dict(parsers, snapshot_path, snapshot):
    """
    ParseDict (see next line) function raises an error in Rabbitmq because it can't recognize protobuf descriptors
    serial_dic = ParseDict(dic_snap, create_empty_snapshot(), ignore_unknown_fields=True)
    so we created a copy (of type dictionary)

    :param parsers: parsers as a dict (as return value of get_parsers())
    :param snapshot_path: a path that will help us to relate a snapshot to a user (users/user_id/snapshots/snapshot_id)
    :param snapshot: protobuf object
    :return: serialized dictionary
    """
    data_paths = save_data(parsers, snapshot)

    dic_snap = MessageToDict(snapshot, including_default_value_fields=True, preserving_proto_field_name=True)
    # replace data attr with data_path
    for parser, data_path in data_paths.items():
        if parser in dic_snap:
            del dic_snap[parser]["data"]
            dic_snap[parser]["data_path"] = str(data_paths[parser])

    # add snapshot path (will be used to relate between the user and its snapshots)
    dic_snap["snapshot_path"] = snapshot_path if snapshot_path else ""
    # print("ds:", dic_snap)

    new_snap_dic = copy.deepcopy(dic_snap)
    return json.dumps(new_snap_dic)


class FlaskInit:
    def __init__(self, publish=None, msg_queue_url=""):
        self.publish = publish
        self.msg_queue_url = msg_queue_url
        self.parsers = get_parsers()
        self.msg_broker = None

    def setup_publisher(self, data, props=None):
        if self.publish:
            self.publish(json.loads(data))
        elif self.msg_queue_url != "":
            with find_msg_broker(self.msg_queue_url) as msq:
                msq.declare_exchange()
                msq.publish(data, props)
        else:
            return False
        return True

    def create_app(self):
        """Initialize the core application."""
        app = Flask(__name__)

        with app.app_context():
            # Include our Routes

            @app.route('/new_user', methods=['POST'])
            def add_user():
                assert request.method == 'POST'

                if not self.setup_publisher(json.dumps(request.form.to_dict())):
                    data = {"error": "no publisher and no message queue url were supplied."}
                    return data

                parsers = [k for k in self.parsers.keys()]
                # return list of available parsers
                return {"parsers": parsers}

            @app.route('/snapshot/<int:user_id>/<int:snapshot_id>', methods=['POST'])
            def add_snapshot(user_id, snapshot_id):

                snapshot_path = Path("users") / str(user_id) / "snapshots" / str(snapshot_id)
                Path(snapshot_path).mkdir(parents=True, exist_ok=True)
                snap_file = request.files["file"].filename
                with open(snap_file, "rb") as f:
                    snap = parse_from(f.read())
                    snap_serial_dic = snapshot_to_dict(self.parsers, str(snapshot_path), snap)

                if not self.setup_publisher(
                        snap_serial_dic,
                        BasicProperties(
                            headers={"snapshot_id": snapshot_id, "user_id": user_id},
                            message_id="snap_"+str(snapshot_id)+"_"+str(user_id))
                ):
                    data = {"error": "no publisher and no message queue url were supplied."}
                    # headers = {"Content-Type": "application/json"}
                    return data
                return ""

            return app


def run_server(host='127.0.0.1', port=8000, publish=None, msg_queue_url=""):
    """
    run server on host:port and publish results with supplied publish function
    otherwise publish snapshots to msgqueue

    :param host:
    :param port:
    :param publish:
    :param msg_queue_url: e.g 'rabbitmq://127.0.0.1:5672/'
    :return:
    """
    if publish is None and msg_queue_url != "":
        flaskinit = FlaskInit(msg_queue_url=msg_queue_url)
    else:
        flaskinit = FlaskInit(publish)
    app = flaskinit.create_app()
    app.run(host, port)

