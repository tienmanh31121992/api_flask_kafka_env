from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy
from elasticsearch import Elasticsearch
from config import Config
from json import dumps, loads
from bson import Timestamp
import redis
import pymongo
import datetime
import time

# import kafka_producer

my_flask = Flask(__name__)
my_flask.config.from_object(Config)
mongo = PyMongo(my_flask)
mysql_db = SQLAlchemy(my_flask)
session = mysql_db.session()
es = Elasticsearch([{'host': Config.ES_HOST, 'port': Config.ES_PORT}])
rds = redis.StrictRedis.from_url(Config.REDIS_URL)
client = pymongo.MongoClient(Config.MONGO_URI)

import models


def myconverter(obj):
    if isinstance(obj, datetime.date):
        return obj.__str__()
    elif isinstance(obj, datetime.datetime):
        return obj.__str__()
    elif isinstance(obj, Timestamp):
        return obj.as_datetime().__str__()


@my_flask.route('/')
def app_info():
    try:
        info = {"""'Kafka Cluster Connected': kafka_producer.check,"""
                'MySQL': str(mysql_db.engine.execute("SELECT VERSION()").fetchall()),
                'MongoDB': loads(dumps(client.admin.command('replSetGetStatus'), default=myconverter)),
                'Elasticsearch': es.cluster.health(),
                'Redis': rds.client_list()}
        return jsonify({'My Flask API': info})
    except:
        return jsonify({'My Flask API': 'app_info() except'})


@my_flask.route('/user', methods=['GET'])
def get_all_user():
    response1 = []
    my_col = mongo.db.user
    for user in my_col.find():
        user['_id'] = str(user['_id'])
        response1.append(user)
    response2 = []
    session.commit()
    for u in session.query(models.User).all():
        response2.append(u.as_dict())
    session.commit()
    return jsonify({'GET_ALL_USER': {'mongo': response1, 'mysql': response2}})


@my_flask.route('/user', methods=['POST'])
def add_user():
    req_data = request.get_json()
    req_data['datecreate'] = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    req_data['username'] = req_data['username'] + str(time.time())[-6:]
    # kafka_producer.send_data('Test', dumps(req_data))
    return jsonify({'INSERTED_USER': req_data})


@my_flask.route('/<database>/user', methods=['PUT'])
def update_user(database):
    req_data = request.get_json()
    response = ''
    if database == 'mongo':
        my_col = mongo.db.user
        my_query = {'username': req_data['username']}
        new_value = {'$set': req_data['new_value']}
        old_data = my_col.find_one(my_query)
        if old_data:
            old_data['_id'] = str(old_data['_id'])
        update_data = my_col.find_one_and_update(my_query, new_value, return_document=True)
        if update_data:
            update_data['_id'] = str(update_data['_id'])
        response = {'database': database, 'new_data': update_data, 'old_data': old_data}
    if database == 'mysql':
        new_value = req_data['new_value']
        user = session.query(models.User).filter_by(username=req_data['username']).first()
        old_data = user.as_dict()
        session.query(models.User).filter_by(username=req_data['username']).update(new_value)
        session.commit()
        response = {'database': database, 'new_data': user.as_dict(), 'old_data': old_data}
    return jsonify({'UPDATED_USER': response})


@my_flask.route('/search/<index>', methods=['GET'])
def search_data(index):
    req_data = request.get_json()
    rdskey = str(req_data)
    value = rds.get(rdskey)
    if value:
        req = {'server': 'redis', 'key': rdskey}
        res = loads(value.decode('utf-8'))
    else:
        req = {'index': index, 'body': req_data}
        res = es.search(index=index,
                        scroll='1m',
                        size=1000,
                        body=req_data)
        page = res #es.search(index=index, scroll='1m', size=1000, body=req_data)
        i = 1
        while len(page['hits']['hits']) > 0:
            scroll_id = page['_scroll_id']
            print('Scrolling...........................')
            mes = 'scroll_id [{}]: {}'.format(i, scroll_id)
            print(mes)
            print(page['hits']['hits'][0]['_id'])
            page = es.scroll(scroll_id=scroll_id, scroll='1m')
            i = i + 1

        rds.setex(rdskey, 60, dumps(res).encode('utf-8'))
    return jsonify({'result': {'request': req, 'response': res}})


@my_flask.route('/<database>/user', methods=['DELETE'])
def delete_user(database):
    req_data = request.get_json()
    response = ''
    if database == 'mongo':
        my_col = mongo.db.user
        rm_data = my_col.find_one_and_delete(req_data)
        if rm_data:
            rm_data['_id'] = str(rm_data['_id'])
        response = {'database': database, 'data': rm_data}
    if database == 'mysql':
        user = session.query(models.User).filter_by(username=req_data['username']).first()
        data = None
        if user:
            session.delete(user)
            session.commit()
            data = user.as_dict()
        response = {'database': database, 'data': data}
    return jsonify({'DELETED_USER': response})


if __name__ == '__main__':
    my_flask.run(host='0.0.0.0', port=Config.APP_PORT, debug=Config.DEBUG)
