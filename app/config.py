import os


class Config(object):
    RUN_IN_DOCKER = True
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pham-tien-manh'
    APP_PORT = os.environ.get('APP_PORT') or 5000
    MONGO_HOST = os.environ.get('MONGO_HOST') or 'localhost'
    MONGO_PORT = os.environ.get('MONGO_PORT') or 27017
    MONGO_DBNAME = os.environ.get('MONGO_DBNAME') or 'kafka'
    MONGO_URI = 'mongodb://{}:{}/{}'.format(MONGO_HOST, MONGO_PORT, MONGO_DBNAME)
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWD = os.environ.get('MYSQL_PASSWD') or '1'
    MYSQL_DBNAME = os.environ.get('MYSQL_DBNAME') or 'kafka'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}/{}?charset=utf8mb4'.format(MYSQL_USER, MYSQL_PASSWD, MYSQL_HOST,
                                                                                   MYSQL_DBNAME)
    SQLALCHEMY_TRACK_MODIFICATIONS = DEBUG

    if RUN_IN_DOCKER:
        BROKERS = [os.environ.get('KAFKA_HOSTNAME1'), os.environ.get('KAFKA_HOSTNAME2'),
                   os.environ.get('KAFKA_HOSTNAME3')]
    else:
        BROKERS = ['localhost:' + str(i) for i in range(9092, 9095)]
