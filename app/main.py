from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy
from config import Config
from json import dumps, loads
import datetime
import time
import kafka_producer
from elasticsearch import Elasticsearch
import redis
import pymongo
from bson import Timestamp

my_flask = Flask(__name__)
my_flask.config.from_object(Config)
mongo = PyMongo(my_flask)
mysql_db = SQLAlchemy(my_flask)
session = mysql_db.session()
es = Elasticsearch([{'host': Config.ES_HOST, 'port': Config.ES_PORT}])
rds = redis.from_url(Config.REDIS_URL)
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
    info = {'Kafka connected': kafka_producer.check,
            'MongoDB': loads(dumps(client.admin.command('replSetGetStatus'), default=myconverter)),
            'MySQL': str(mysql_db.engine.execute("SELECT VERSION()").fetchall()), 'Elasticsearch': es.cluster.health(),
            'Redis': rds.client_list()}
    return jsonify({'My Flask API': info})


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
    kafka_producer.send_data('Test', dumps(req_data))
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


@my_flask.route('/<database>/user', methods=['GET'])
def find_user(database):
    req_data = request.get_json()
    return jsonify({'result': req_data})


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
