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
    day = db.Column(db.DateTime, default='1/1/2000', nullable=False)
    mean_temp = db.Column(db.Float)
    high = db.Column(db.Float)
    time_h = db.Column(db.String(100))
    low = db.Column(db.Float)
    time_l = db.Column(db.String(100))
    max_rh = db.Column(db.Float)
    min_rh = db.Column(db.Float)
    rain = db.Column(db.Float)
    avg_wind_speed = db.Column(db.Float)
    high_w = db.Column(db.Float)
    time_w = db.Column(db.String(100))
    dom_dir = db.Column(db.String(100))

    def __repr__(self):
        return f"{self.id}:{self.DAY}:{self.MEAN_TEMP}"