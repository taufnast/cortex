import click
import json
from ._init_parser import parse, run_parser, setup_consumer, setup_publisher


@click.group()
def cli():
    pass


###################
# NOT IMPLEMENTED
###################
@cli.command(name="run-parser")
@click.argument('parser_name', type=click.STRING)
@click.argument('msg_queue_url', type=click.STRING)
def cli_run_parse(parser_name, msg_queue_url):
    setup_consumer(msg_queue_url)
    pass
    # run_parser(parser_name, data)


@cli.command(name="parse")
@click.argument('parser_name', type=click.STRING)
@click.argument('raw_data_path', type=click.Path(exists=True))
def cli_parse(parser_name, raw_data_path):
    """read data from supplied file and publish it to msgqueue (optionally, save it to some file)"""
    with open(raw_data_path, "r") as f:
        data = json.load(f)

    parsed_data = parse(parser_name, data)
    if parsed_data is None:
        return None

    dump_data = json.dumps(parsed_data)
    click.echo(dump_data)

    # not implemented - we can't use the same exchange!
    # url = 'rabbitmq://127.0.0.1:5672/'
    # setup_publisher(url, dump_data)


if __name__ == '__main__':
    cli()
