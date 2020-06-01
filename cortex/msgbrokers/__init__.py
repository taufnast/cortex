from .rabbitmq import RabbitMQ

# it was preferable to create a local dict of msgq classes as ther is only one
# but it can be updated easily
# on some point we may want to create a config yaml file containing all the msgqs
msg_brokers = {"rabbitmq": RabbitMQ}


def find_msg_broker(url):
    for scheme, cls in msg_brokers.items():
        if url.startswith(scheme):
            if "//" in url:  # url = 'rabbitmq://127.0.0.1:5672/'
                _, url = url.split("//")
            return cls(url)

    raise ValueError(f'invalid url: {url}')
