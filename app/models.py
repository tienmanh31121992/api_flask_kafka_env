from main import mysql_db
from sqlalchemy import INTEGER, String


class User(mysql_db.Model):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}
    _id = mysql_db.Column(INTEGER, primary_key=True, autoincrement=True)
    username = mysql_db.Column(String(50), nullable=False)
    password = mysql_db.Column(String(50), nullable=False)
    birthday = mysql_db.Column(String(20))
    fullname = mysql_db.Column(String(255))
    datecreate = mysql_db.Column(String(100))

    def __str__(self):
        return '<User: {}, ID: {}>'.format(self.username, self._id)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __init__(self, from_dict):
        if from_dict['_id']:
            del from_dict['_id']
        for key in from_dict:
            setattr(self, key, from_dict.get(key))


if __name__ == '__main__':
    mysql_db.create_all()
