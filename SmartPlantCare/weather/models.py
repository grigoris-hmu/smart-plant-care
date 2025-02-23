from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint
#from sqlalchemy import UniqueConstraint
from datetime import datetime
from .. import db

class WeatherStation(db.Model):
    __tablename__ = 'weather_station'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='weather_station_pk'),
        ForeignKeyConstraint(['prefecture'], ['prefecture.id']),
        ForeignKeyConstraint(['area'], ['area.id'])      
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prefecture = db.Column(db.Integer, db.ForeignKey('prefecture.id'), nullable=False)
    area = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    url = db.Column(db.String(200))

    def __repr__(self):
        return f"{self.id}:{self.prefecture}:{self.area}:{self.url}"


class MonthlyWeather(db.Model):
    __tablename__ = 'monthly_weather'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='monthly_weather_pk'),
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    DAY = db.Column(db.DateTime, default='1/1/2000', nullable=False)
    MEAN_TEMP = db.Column(db.Float)
    HIGH = db.Column(db.Float)
    TIME_H = db.Column(db.String(100))
    LOW = db.Column(db.Float)
    TIME_LOW = db.Column(db.String(100))
    MAX_RH = db.Column(db.Float)
    MIN_RH = db.Column(db.Float)
    RAIN = db.Column(db.Float)
    AVG_WIND_SPEED = db.Column(db.Float)
    HIGH_W = db.Column(db.Float)
    TIM_W = db.Column(db.String(100))
    DOM_DIR = db.Column(db.String(100))

    def __repr__(self):
        return f"{self.id}:{self.DAY}:{self.MEAN_TEMP}"