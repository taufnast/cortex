import click
from flask import Flask
from flask import request


@click.group()
def cli():
    pass


'''
We are planing to distinguish between the clients by user_id

We have to be able to pass publish to our routs
it can be done with the 'g' Flask object?
'''


class FlaskInit:
    def __init__(self, publish=None, msg_queue_url=""):
        self.publish = publish
        self.msg_queue_url = msg_queue_url

    def create_app(self):
        """Initialize the core application."""
        app = Flask(__name__)

        with app.app_context():
            # Include our Routes
            # from . import routes

            @app.route('/new_user', methods=['POST'])
            def add_user():
                assert request.method == 'POST'
                print(request.form["user_id"])
                # we may return list of parsers as well
                # headers = {"Content-Type": "application/json"}
                # return make_response(data, 200, headers=headers)
                print("from usr")
                if self.publish:
                    self.publish(request.form.to_dict())
                # return the available parsers
                return {"res": 200}

            @app.route('/snapshot/<int:user_id>', methods=['POST'])
            def add_snapshot(user_id):
                print("from snap")
                print(user_id)
                return ""

            return app


@click.command()
@click.option('--host', '-h', default='127.0.0.1', help='Host')
@click.option('--port', '-p', default=8000, help='Port')
@click.argument('msg_queue_url', type=click.types.STRING)
# TODO: remove default value for publish
def run_server(host, port, publish = None, msg_queue_url = ""):
    '''Run server by calling for run_server with host, port and 'URL to a message queue'''
    flaskinit = FlaskInit(publish, msg_queue_url)
    app = flaskinit.create_app()
    app.run(host, port)


def print_message(message):
    print(message)


cli.add_command(run_server())

if __name__ == '__main__':
    cli()
    # run_server('127.0.0.1', 8000, print_message)