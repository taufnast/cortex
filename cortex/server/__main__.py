from cortex.server import run_server
import click


@click.group()
def cli():
    pass


@cli.command(name="run-server")
@click.option('--host', '-h', default='127.0.0.1', help='Host')
@click.option('--port', '-p', default=8000, help='Port')
@click.argument('msg_queue_url', type=click.STRING)
def cli_run_server(host, port, msg_queue_url):
    """Run server by calling for run-server with host, port and URL to a message queue"""
    run_server(host=host, port=port, msg_queue_url=msg_queue_url)


if __name__ == '__main__':
    cli()