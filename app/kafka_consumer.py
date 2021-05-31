from config import Config
from main import mongo, session
from kafka import KafkaConsumer
from json import loads
import models


consumer = KafkaConsumer(bootstrap_servers=Config.BROKERS, auto_offset_reset='latest', enable_auto_commit=True,
                         auto_commit_interval_ms=500, consumer_timeout_ms=-1, group_id='data',
                         value_deserializer=lambda x: x.decode('utf-8'))


def insert_data(topic_name, table_name):
    consumer.subscribe(topic_name)
    my_col = mongo.db[table_name]
    for msg in consumer:
        req_data = msg.value
        data = loads(req_data)
        new_id = my_col.insert_one(data).inserted_id
        new_data = my_col.find_one({'_id': new_id})

        user = models.User(from_dict=data)

        # user = models.User(username=data['username'], password=data['password'],
        #                    fullname=data['fullname'], birthday=data['birthday'],
        #                    datecreate=data['datecreate'])
        session.add(user)
        session.commit()
        new_user = models.User.query.filter_by(username=user.username).first()

        print('<User: {}, ID: {}> added to collection {}'.format(new_data['username'], new_data['_id'], table_name),
              flush=True)
        print('{} added to table {}'.format(new_user, table_name), flush=True)


if __name__ == '__main__':
    insert_data('Test', 'user')
