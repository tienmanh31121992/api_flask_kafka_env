from config import Config
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers=Config.BROKERS)
check = producer.bootstrap_connected()


def send_data(topic_name, value):
    producer.send(topic_name, value=value.encode('utf-8'))
    producer.flush()
