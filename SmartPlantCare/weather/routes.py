from flask import render_template, request, session
#from flask import flash, redirect, url_for, abort
from flask_login import login_required
#from flask_login import login_user, logout_user, current_user
from flask_babel import _
import requests
from bs4 import BeautifulSoup
import pandas as pd
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.models import ColumnDataSource,HoverTool
from . import weather
from .models import WeatherStation, MonthlyWeather
from ..crop.models import Crop
from SmartPlantCare import app
from .. import db


def get_weather(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:

        html_text = requests.get(url ,headers=headers).text
        soup = BeautifulSoup(html_text, "html.parser")

        table = soup.find("div", class_="col_sub dist boxshadow realtime")
        lines = table.find_all("div", class_="line")

        data = {}

        for line in lines:
                key = line.find("div", class_="lleft").find("span").get_text(strip=True)
                value = line.find("div", class_="lright").find("span").get_text(strip=True)
                data[key] = value

    except Exception as e:
        print("error:",e)
        pass

    return data

@weather.route("/get_weather_data/<int:crop_id>", methods=['GET'])
@login_required
def get_weather_data(crop_id):

    crop = Crop.query.get_or_404(crop_id)

    weather_station2 = (
            db.session.query(WeatherStation.url)
            .join(Crop, WeatherStation.area == Crop.area)
            .filter(Crop.id == crop_id).one_or_none)

    print("weather_station")
    print(weather_station2)

    #weather_data = get_weather(weather_station.url)
    weather_data = get_weather('https://penteli.meteo.gr/stations/heraclion/')

    return render_template("weather_data.html", crop=crop, weather_data=weather_data)


@weather.route("/temperature_graph/<int:crop_id>", methods=['GET'])
@login_required
def temperature_graph(crop_id):

    crop = Crop.query.get_or_404(crop_id)

    weather_station = (
            db.session.query(MonthlyWeather.DAY, MonthlyWeather.HIGH,MonthlyWeather.LOW,MonthlyWeather.MEAN_TEMP)
            .order_by(MonthlyWeather.DAY.asc())
            .filter(
                    MonthlyWeather.DAY.isnot(None),
                    MonthlyWeather.HIGH.isnot(None),
                    MonthlyWeather.LOW.isnot(None),
                    MonthlyWeather.MEAN_TEMP.isnot(None)
                 )
            .all()
    )

    date = [i[0] for i in weather_station]
    high = [i[1] for i in weather_station]
    mid = [i[3] for i in weather_station]
    low = [i[2] for i in weather_station]

    print(date)

    source = ColumnDataSource(data=dict(
        x = date,
        y1 = high,
        y2 = mid,
        y3 = low
        ))
    
    hover_tool = HoverTool(
      tooltips = [
       ('Ημερομηνία', '@x{%F}'),
       ('Μέγιστη Θερμοκρασία', '@y1{0.0}'),
       ('Μέση Θερμοκρασία', '@y2{0.0}'),
       ('Ελάχιστη Θερμοκρασία', '@y3{0.0}')
     ],
      formatters={
           '@x' : 'datetime'
      },
      mode = "mouse"
    )

     
    t = figure(title = "Θερμοκρασία", x_axis_label = "Ημερομηνία",x_axis_type = "datetime", y_axis_label = "Θερμοκρασία",width = 600, height = 350)
    t.line('x','y1', legend_label = "Μέγιστη Θερμοκρασία",color ='red', line_width =2,source=source)
    t.scatter('x','y1',color = 'red',source=source)
    t.line('x','y2', legend_label = "Μέση Θερμοκρασία",color = 'yellow', line_width =2,source=source)
    t.scatter('x','y2',color = 'yellow',source=source)
    t.line('x','y3', legend_label = "Χαμηλή Θερμοκρασία",color = 'blue', line_width =2,source=source)
    t.scatter('x','y3',color = 'blue',source=source)
    t.add_tools(hover_tool)
    script, div = components(t)
    resources = CDN.render() 

    return render_template("temperature_data.html", crop=crop,script=script,div=div,resources=resources)


@weather.route("/rain_graph/<int:crop_id>", methods=['GET'])
@login_required
def rain_graph(crop_id):

    crop = Crop.query.get_or_404(crop_id)

    weather_station = (
            db.session.query(MonthlyWeather.DAY, MonthlyWeather.MAX_RH,MonthlyWeather.MIN_RH,MonthlyWeather.RAIN)
            .order_by(MonthlyWeather.DAY.asc())
            .filter(
                    MonthlyWeather.DAY.isnot(None),
                    MonthlyWeather.MAX_RH.isnot(None),
                    MonthlyWeather.MIN_RH.isnot(None),
                    MonthlyWeather.RAIN.isnot(None)
                 )
            .all()
    )

    date = [i[0] for i in weather_station]
    high = [i[1] for i in weather_station]
    mid = [i[2] for i in weather_station]
    low = [i[3] for i in weather_station]

    print(date)

    source = ColumnDataSource(data=dict(
        x = date,
        y1 = high,
        y2 = mid,
        y3 = low
        ))
    
    hover_tool = HoverTool(
      tooltips = [
       ('Ημερομηνία', '@x{%F}'),
       ('Μέγιστη Υγρασία', '@y1{0.0}%'),
       ('Ελάχιστη Υγρασία', '@y2{0.0}%'),
       ('Βροχή', '@y3{0.0}')
     ],
      formatters={
           '@x' : 'datetime'
      },
      mode = "mouse"
    )

     
    r = figure(title = "Υγρασία/Βροχή", x_axis_label = "Ημερομηνία",x_axis_type = "datetime", y_axis_label = "Υγρασία/Βροχή",width = 600, height = 350)
    r.line('x','y1', legend_label = "Μέγιστη Υγρασία(%)",color ='red', line_width =2,source=source)
    r.scatter('x','y1',color = 'red',source = source)
    r.line('x','y2', legend_label = "Ελάχιστη Υγρασία(%)",color = 'blue', line_width =2,source = source)
    r.scatter('x','y2',color = 'blue',source = source)
    r.line('x','y3', legend_label = "Βροχή(mm)",color = 'yellow', line_width =2,source=source)
    r.scatter('x','y3',color = 'yellow',source=source)
    r.add_tools(hover_tool)
     

    script, div = components(r)
   

    return render_template("rain_data.html", crop=crop,script=script,div=div)