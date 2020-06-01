from cortex.client import upload_sample
import click


@click.group()
def cli():
    pass


@cli.command(name="upload-sample")
@click.option('--host', '-h', default='127.0.0.1', help='Host')
@click.option('--port', '-p', default=8000, help='Port')
@click.argument('path', type=click.Path(exists=True))
def cli_upload_sample(host, port, path):
    upload_sample(host=host, port=port, path=path)


if __name__ == '__main__':
    cli()