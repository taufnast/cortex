# from .rabbitmq import RabbitMQ
#
# msg_brokers = {"rabbitmq": RabbitMQ}
#
# #
# # class MsgBroker:
# #     def __init__(self, url):
# #         self.msgBroker = find_msg_broker(url)
# #
# #     def publish(self, msg):
# #         pass
# #
# #     def consume(self):
# #         pass
#
#
# def find_msg_broker(url):
#     for scheme, cls in msg_brokers.items():
#         if url.startswith(scheme):
#             if "//" in url:  # url = 'rabbitmq://127.0.0.1:5672/'
#                 _, url = url.split("//")
#             return cls(url)
#
#     raise ValueError(f'invalid url: {url}')
