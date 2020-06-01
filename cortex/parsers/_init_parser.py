import inspect
import json
import os
import sys
from cortex.loader import load_modules
from cortex.msgbrokers import find_msg_broker
from pathlib import Path

WARNING_PREFIX = "Warning:"
ERROR_PREFIX = "Error:"

"""
aspect-oriented programming:
Collect all the functions (in current subpackage) that starts with parse_
and all the classes that ends with Parser
"""
# parsers = { class/function.tag: class/function }


class ParsersCollector:
    def __init__(self):
        self.imported_modules = self._load_modules()
        self.parsers = {}  # { class/function.tag: class/function }
        self._collect_parsers()
        # print(self.parsers)

    def _load_modules(self):
        """
        traverse current directory and load import all the modules
        :return: list of imported modules names
        """
        imported_modules = load_modules(os.path.dirname(__file__))
        # print(imported_modules)
        return imported_modules

    def _collect_parsers(self):  # , imported_modules):
        """
        for each imported module traverse all member so that:
        each class which name ends with "Parser" and
        each function which name starts with parse_ will be added to
        parsers dictionary.
        :param imported_modules:
        :return: void
        """
        for mod in self.imported_modules:
            for name, value in inspect.getmembers(sys.modules[mod]):
                if inspect.isclass(value) and name.endswith("Parser"):
                    # print(name)
                    obj = value()
                    try:
                        self.parsers[obj.tag] = obj.parse
                    except AttributeError:
                        print(f'{WARNING_PREFIX} class {name} has no tag attribute. This parser will be skipped.')
                elif inspect.isfunction(value) and name.startswith("parse_"):
                    # print(name)
                    try:
                        self.parsers[value.tag] = value
                    except AttributeError:
                        print(f'{WARNING_PREFIX} function {name} has no tag attribute. This parser will be skipped.')

    def find_parser(self, parser_name, data):
        """
        Search for parser among imported modules
        VIP: this function assumes that each parser expects context object to be the first
        parameter and data as its second

        :param parser_name: - string
        :param data: data as consumed from the message queue
        :return: If parser is found return parser object, otherwise return None
        """
        for name, parser in self.parsers.items():
            if name == parser_name:
                context = Context()
                return parser(context, data)
        return None


def parse(parser_name, data):
    try:
        parsed_data = ParsersCollector().find_parser(parser_name, data)
        if parsed_data is None:
            print(f'{ERROR_PREFIX} supplied parser name - {parser_name} was not found.')
        return parsed_data
    except TypeError:
        print(f'{ERROR_PREFIX} parser - {parser_name} TypeError - params may differ from expected: context, data.')
        return None


def run_parser(parser_name, data):
    # print(__file__)
    parsed_data = parse(parser_name, data)
    print(parsed_data)
    url = 'rabbitmq://127.0.0.1:5672/'
    setup_publisher(url, json.dumps(parsed_data))


class Context:
    def __init__(self, snapshot_path="/tmp"):
        self.snapshot_path = snapshot_path
        self.msg_broker = None

    def path(self, file_name, snapshot_path=""):
        """
        Define a path for saving the file.
        We updated each snapshot structure so that it includes a path.
        It is preferable that all the data is saved using this path.
        However, the 'snapshot_path' was made flexible so that it can easily be changed.

        :param file_name: string
        :param snapshot_path: as included in snapshot
        :return: full path to the supplied file
        """
        if snapshot_path:
            self.snapshot_path = Path(snapshot_path)
            Path(snapshot_path).mkdir(parents=True, exist_ok=True)
        return self.snapshot_path / file_name

    def save(self, file_name, data):
        with open(self.path(file_name), "w") as f:
            f.write(data)


###################
# NOT IMPLEMENTED
###################
# We should create another exchange/change type
def setup_publisher(url, data, props=None):
    pass
    # with find_msg_broker(url) as msq:
    #     msq.declare_exchange()
    #     msq.publish(data, props)


def setup_consumer(url, callback=None):
    with find_msg_broker(url) as msq:
        msq.declare_exchange()
        queue_name = msq.queue_declare()
        if callback is None:  # message broker has a default callback function
            msq.consume(queue_name)
        else:
            msq.consume(queue_name, callback=callback)
