import pika


def callback(method, properties, body):
    print(" [x] %r:%r _ %r" % (method.routing_key, body, properties))


class RabbitMQ:
    def __init__(self, url):
        if ":" in url:
            self.host, self.port = url.strip("/").split(":")
            params = pika.ConnectionParameters(self.host, self.port)
        else:
            params = pika.ConnectionParameters(url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.exchange = 'snapshot'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()

    def declare_exchange(self):
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='fanout')

    def queue_declare(self):
        result = self.channel.queue_declare(queue='', exclusive=True, durable=True)
        queue_name = result.method.queue
        self.channel.queue_bind(exchange=self.exchange, queue=queue_name)

        print(' [*] Waiting for logs. To exit press CTRL+C')
        return queue_name

    def publish(self, msg, props=None):
        self.channel.basic_publish(exchange='snapshot', routing_key='', body=msg, properties=props)
        if "snapshot_path" in msg:
            out = msg["snapshot_path"]
        elif "user_id" in msg:
            out = msg["user_id"]
        else:  # unexpected format ?
            out = msg
        print(" [x] Sent %r" % out)

    def consume(self, queue_name, callback=callback):
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=True)
        self.channel.start_consuming()
