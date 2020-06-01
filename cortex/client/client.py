import requests
from pathlib import Path
from secrets import token_hex
from cortex.reader import Reader, serialize

ERROR_PREFIX = "ERROR: "
TIMEOUT_PREFIX = "TIMEOUT: "


def validate_attr(attr, default_val, path):
    if attr == default_val:
        print(ERROR_PREFIX, "No {} was supplied. Please recheck the data - {}".format(attr, path))
        return False
    return True


def send_request(url, data, filename="", headers=None, timeout=10):
    try:
        if filename != "":
            files = {'file': (str(filename), open(filename, 'rb'))}
            r = requests.post(url, data=data, files=files, timeout=timeout)
        else:
            r = requests.post(url, data=data, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout:
        print(TIMEOUT_PREFIX, "Couldn't upload the data. Please, try again latter.")
        return None
    except (requests.exceptions.RequestException, ConnectionError) as e:
        # catastrophic failure
        print(ERROR_PREFIX, "Server is currently unavailable.")
        # print(e)
        return None

    if r.status_code != requests.codes.ok:
        print(ERROR_PREFIX, "Couldn't upload the data. Response status:", r.status_code)
        return None
    return r


def upload_user(base_url, user):
    url = "{}/new_user".format(base_url)
    r = send_request(url, user)
    if r:
        try:
            config = r.json()
            if "parsers" in config:
                return config["parsers"]
            if "error" in config:
                print(ERROR_PREFIX, config["error"])
        except ValueError:  # json parsing error
            print(ERROR_PREFIX, "couldn't parse json. Print response as text:", r.text)
    return None


def upload_snapshot(base_url, user_id, snapshot, snapshot_id, parsers=None):
    url = "{}/snapshot/{}/{}".format(base_url, user_id, snapshot_id)
    # print("snapshot fields list:", len(snapshot.ListFields()))

    acceptable_fields = []  # snapshot fields that can be parsed
    if parsers is not None:
        for parser in parsers:
            try:
                if snapshot.HasField(parser):
                    acceptable_fields.append(parser)
            except ValueError:
                # redundant parser
                pass

    # print("accept", acceptable_fields)

    # send a snapshot as file
    # attempt to send serialized proto object as is resulted in error
    # r = send_request(url, snapshot.SerializeToString())  # too big
    # create tmp file
    snapfiles_path = Path("/tmp/snapfiles/")
    snapfiles_path.mkdir(parents=True, exist_ok=True)
    snapfile_path = snapfiles_path / ("snap_" + token_hex(5) + ".bytes")
    with open(snapfile_path, "wb") as f:
        f.write(serialize(snapshot))
    # send file to server
    r = send_request(url, data=None, filename=snapfile_path)

    if r:
        try:
            resp = r.json()
            if "error" in resp:
                print(ERROR_PREFIX, resp["error"])
        except ValueError:  # json parsing error
            pass
            # resp = r.text
            # print("Couldn't parse json. Print response as text:", resp)


def upload_sample(host='127.0.0.1', port=8000, path=""):
    """
    Upload a sample by providing host, port and path to gz file.
    Gz file is expected to include user data and a list of snapshots serialized with google protobuf.
    For more info please see cortes.proto file.

    :param host:
    :param port:
    :param path: path to gz data file
    :return: void
    """
    with Reader(path) as reader:
        new_user = {}
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

        base_url = "" if "http" in host else "http://"
        base_url += "{}:{}".format(host, port)
        parsers = upload_user(base_url, new_user)

        if parsers is not None:  # if no error (on error, parsers = None)
            snapshot_id = 1
            for snapshot in reader:
                # print(snapshot.datetime, snapshot.color_image.width, snapshot.color_image.height)
                upload_snapshot(base_url, user_id, snapshot, snapshot_id, parsers)
                snapshot_id += 1
