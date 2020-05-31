import click
import numpy as np
import yaml
import json
import copy
from flask import Flask
from flask import request
from cortex.msgbrokers.msgbroker import find_msg_broker
from cortex.reader import parse_from, create_empty_snapshot
from google.protobuf.json_format import MessageToDict, MessageToJson, ParseDict
from pathlib import Path
from secrets import token_hex


def get_parsers():
    with open('config/parsers.yaml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        # print(data)
        if "parsers" in data:
            return data["parsers"]
    return {}


def traverse(dic, field):
    try:
        for desc, val in field.ListFields():
            # print("inner desc", desc.name)
            dic[desc.name] = traverse(dic.get(desc.name, {}), val)
    except AttributeError:
        # print("I'm not iterable!", field)
        print("base type", type(field))
        return field


def save_data(parsers, snapshot):
    """save data is looking for 'data' field (as it stores the 'big data', based on the cortex.proto)"""
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
    data_paths = save_data(parsers, snapshot)

    dic_snap = MessageToDict(snapshot, including_default_value_fields=True, preserving_proto_field_name=True)
    # print(dic_snap.keys())
    # print(type(dic_snap["color_image"]["data"]))
    # print(type(dic_snap["depth_image"]["data"]))

    for parser, data_path in data_paths.items():
        if parser in dic_snap:
            del dic_snap[parser]["data"]
            dic_snap[parser]["data_path"] = dic_snap[parser]

    # add snapshot path (will be used to relate between the user and its snapshots)
    dic_snap["snapshot_path"] = snapshot_path if snapshot_path else ""
    print("ds:", dic_snap)
    print(type(dic_snap))
    some = ParseDict(dic_snap, create_empty_snapshot(), ignore_unknown_fields=True)
    print(some)
    # new_snap_dic = copy.deepcopy(dic_snap)
    return some


'''
We are planing to distinguish between the clients by user_id
'''


class FlaskInit:
    def __init__(self, publish=None, msg_queue_url=""):
        self.publish = publish
        self.msg_queue_url = msg_queue_url
        self.parsers = get_parsers()
        self.msg_broker = None

    def setup_publisher(self, data, props=None):
        if self.publish:
            self.publish(json.load(data))
        elif self.msg_queue_url != "":
            # pass
            if self.msg_broker is None:
                self.msg_broker = find_msg_broker(self.msg_queue_url)
                self.msg_broker.declare_exchange()
            # self.msg_broker.publish(json.dumps(data))
            self.msg_broker.publish(data, props)
                # with find_msg_broker(self.msg_queue_url) as msq:
                #     msq.exchange_declare()
                #     msq.publish(json.dumps(data))
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
                print(request.form["user_id"])

                # headers = {"Content-Type": "application/json"}
                # return make_response(data, 200, headers=headers)
                print("from usr")
                if not self.setup_publisher(json.dumps(request.form.to_dict())):
                    data = {"error": "no publisher and no message queue url were supplied."}
                    return data

                parsers = [k for k in self.parsers.keys()]
                # return list of available parsers
                return {"parsers": parsers}

            @app.route('/snapshot/<int:user_id>/<int:snapshot_id>', methods=['POST'])
            def add_snapshot(user_id, snapshot_id):
                print("from snap", self.publish, self.msg_queue_url)
                print(user_id)

                snapshot_path = Path("users") / str(user_id) / "snapshots" / str(snapshot_id)
                Path(snapshot_path).mkdir(parents=True, exist_ok=True)
                snap_file = request.files["file"].filename
                with open(snap_file, "rb") as f:
                    snap = parse_from(f.read())
                    snap_dic = snapshot_to_dict(self.parsers, snapshot_path, snap)  # TODO: it's not json yet!!!!!!!!!!
                    print("new snap", type(snap_dic), snap_dic)
                    props = {"arguments": {"user_id": user_id, "snapshot_id": snapshot_id}, "content-type": "application/protobuf"}
                if not self.setup_publisher(snap_dic, props):
                    data = {"error": "no publisher and no message queue url were supplied."}
                    # headers = {"Content-Type": "application/json"}
                    return data
                return ""

            return app


@click.group()
def cli():
    pass


# context_settings=dict(
#     ignore_unknown_options=True,
# )
# @cli.command(from_function_signature=True)

@cli.command(name="run-server")
@click.option('--host', '-h', default='127.0.0.1', help='Host')
@click.option('--port', '-p', default=8000, help='Port')
@click.argument('msg_queue_url', type=click.STRING)
def cli_run_server(host, port, msg_queue_url):
    """Run server by calling for run-server with host, port and URL to a message queue"""
    run_server(host=host, port=port, msg_queue_url=msg_queue_url)
    # flaskinit = FlaskInit(msg_queue_url=msg_queue_url)


def run_server(host='127.0.0.1', port=8000, publish=None, msg_queue_url=""):
    if publish is None and msg_queue_url != "":
        flaskinit = FlaskInit(msg_queue_url=msg_queue_url)
    else:
        flaskinit = FlaskInit(publish)
    app = flaskinit.create_app()
    app.run(host, port)


if __name__ == '__main__':
    cli()
    # run_server('127.0.0.1', 8000, print_message)
