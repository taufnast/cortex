#!/usr/bin/env python3

## (! /usr/bin/python)
import click
import requests
from cortex.reader import Reader

ERROR_PREFIX = "ERROR: "
TIMEOUT_PREFIX = "TIMEOUT: "


@click.group()
def cli():
    pass


def validate_attr(attr, default_val, path):
    if attr == default_val:
        print(ERROR_PREFIX, "No {} was supplied. Please recheck the data - {}".format(attr, path))
        return False
    return True


def send_request(url, data, timeout = 10):
    try:
        r = requests.post(url, data=data, timeout=timeout)
    except requests.exceptions.Timeout:
        print(TIMEOUT_PREFIX, "Couldn't upload the data. Please, try again latter.")
        return None
    except (requests.exceptions.RequestException, ConnectionError) as e:
        # catastrophic failure
        print(ERROR_PREFIX, "Server is currently unavailable.")
        print(e)
        return None

    if r.status_code != requests.codes.ok:
        print(ERROR_PREFIX, "Couldn't upload the user. Response status:", r.status_code)
        return None
    return r


def upload_user(base_url, user):
    url = "{}/new_user".format(base_url)
    r = send_request(url,user)
    if r:
        try:
            config = r.json()
        except ValueError:  # json parsing error
            config = r.text
        print("resp:", config)


def upload_snapshot(base_url, user_id, snapshot):
    url = "{}/snapshot/{}".format(base_url, user_id)
    prepared_snapshot = {}
    try:
        prepared_snapshot["datetime"] = snapshot.datetime
    except AttributeError:
        pass

    r = send_request(url, prepared_snapshot)
    if r:
        try:
            config = r.json()
        except ValueError:  # json parsing error
            config = r.text
        print("resp:", config)


@click.command()
@click.option('--host', '-h', default='127.0.0.1', help='Host')
@click.option('--port', '-p', default=8000, help='Port')
@click.argument('path', type=click.Path(exists=True))
def upload_sample(host, port, path):
    """
    Upload a sample by providing host, port and path to gz file.
    Gz file is expected to include user data and a list of snapshots serialized with google protobuf.
    For more info please see cortes.proto file.
    """
    with Reader(path) as reader:
        # reader = Reader(path)
        new_user = {}
        # print(len(reader.__dict__["user"]))
        print(reader.__dict__["user"])
        user_id = reader.user_id
        if not validate_attr(user_id, -1, path):
            return
        new_user["user_id"] = user_id

        username = reader.username
        if not validate_attr(username, "", path):
            return
        new_user["username"] = username

        birthday = reader.birthday
        if not validate_attr(birthday, None, path):
            return
        try:
            birthday_timestamp = int(birthday.timestamp())
        except OverflowError:
            print(ERROR_PREFIX, "datetime object raised OverflowError. Please recheck supplied data -", path)
            return
        new_user["birthday"] = birthday_timestamp

        gender = reader.gender
        if not validate_attr(gender, "", path):
            return
        new_user["gender"] = gender

        print(reader.user_id)
        print(reader.username)
        print(reader.gender)
        print(reader.birthday)
        # http:// is required
        base_url = "" if "http" in host else "http://"
        base_url += "{}:{}".format(host, port)
        upload_user(base_url, new_user)

        for snapshot in reader:
            print(snapshot.datetime, snapshot.color_image.width, snapshot.color_image.height)
            upload_snapshot(base_url, user_id, snapshot)
            break


cli.add_command(upload_sample)

if __name__ == '__main__':
    cli()

    # upload_sample(host='127.0.0.1', port=8000, path='/home/nast/univer/advanced_systems_design/sample.mind.gz')
