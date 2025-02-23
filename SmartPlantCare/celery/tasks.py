from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from ..celery.email_notifier import EmailNotifier


@shared_task
def check_sensor_data_thresholds():
    from .. import celery
    from ..user.models import User
    from ..alert.models import Alert
    from ..sensor.models import Sensor, SensorData
    from ..crop.models import Crop
    from .. import db
    from .. import app

    #sensor settings
    MOISTURE_SENSOR_THRESHOLD_MAX = app.config['MOISTURE_SENSOR_THRESHOLD_MAX']
    MOISTURE_SENSOR_THRESHOLD_MIN = app.config['MOISTURE_SENSOR_THRESHOLD_MIN']

    notifier = EmailNotifier(
        app.config['NOTIFICATION_SENDER_EMAIL_ADDRESS'],
        app.config['NOTIFICATION_EMAIL_PASSWORD'],
        app.config['NOTIFICATION_SMTP_SERVER'],
        app.config['NOTIFICATION_SMTP_SERVER_PORT']
        )

    print("Alert-Notification Daemon(task) periodic execution.")

    try:
        # Get all crops
        crops =  db.session.query(Crop).all()

        for crop in crops:
            # Get the latest sensor data for the crop
            latest_sensor_data = (
                db.session.query(SensorData)
                .join(Sensor, SensorData.sensor_id == Sensor.id)
                .filter(Sensor.crop_id == crop.id, SensorData.processed==False)
                .order_by(SensorData.date_time.desc())
                .first()
            )
            print("##### latest_sensor_data #####")
            print(latest_sensor_data)
            # Check if the latest sensor value exceeds the threshold
            if latest_sensor_data and (
                latest_sensor_data.value < MOISTURE_SENSOR_THRESHOLD_MIN
                or latest_sensor_data.value > MOISTURE_SENSOR_THRESHOLD_MAX):
                # Get the user associated with the crop
                user = db.session.query(User).filter_by(id=crop.user_id).first()
                if user:
                    recipient_email = user.email

                    # Create an alert
                    alert = Alert(
                        crop_id=crop.id,
                        threshold_type="sensor_value",
                        threshold_value=latest_sensor_data.value,
                        action_taken="Send notification email for threshold exceeded",
                        timestamp=datetime.utcnow(),
                    )
                    db.session.add(alert)

                    # Send email notification
                    subject = "SmartPlantCare Alert Notification"
                    body = f"Alert for your crop {crop.name}: Sensor value {latest_sensor_data.value} exceeded the threshold."
                    notifier.send_email(recipient_email, subject, body)

                    print(f"Email sent to: {recipient_email}")
                    print(f"Alert for crop: {crop.name} with sensor value: {latest_sensor_data.value}")

                    # Mark the sensor data as processed
                    latest_sensor_data.processed = True

        # Commit the session
        db.session.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        db.session.rollback()
    finally:
        db.session.close()



@shared_task
def check_watering():
    from .. import celery
    from ..crop.models import Crop
    from .. import db
    from ..irrigation.models import regionBulletin, regionBulletinData, irrigationData
    from ..sensor.models import Valve

    units_per_minute = 10
    try:
        # Get all crops
        crops = db.session.query(Crop).all()

        for crop in crops:
            print(f"Processing crop: {crop.name}")

            # Get the current week dates (Sunday to Saturday)
            today = datetime.utcnow()
            start_of_week = today - timedelta(days=today.weekday() + 1)  # Last Sunday
            end_of_week = start_of_week + timedelta(days=6)  # Next Saturday

            # Set time to 00:00:00
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_week = end_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

            print(f"Start of Week: {start_of_week}")
            print(f"End of Week: {end_of_week}")

            # Query to get the irrigation need for the specific crop
            irrigation_data_query = (
                db.session.query(regionBulletinData)
                .join(regionBulletin, regionBulletin.id == regionBulletinData.bulletin)
                .filter(
                    regionBulletin.start_date >= start_of_week,
                    regionBulletin.end_date <= end_of_week,
                    regionBulletinData.prefecture == crop.prefecture,
                    regionBulletinData.crop_type == crop.crop_type,
                    regionBulletinData.soil_type == crop.soil_type,
                    regionBulletinData.area == crop.area
                )
                .all()
            )
           
            #get Valve associated.
            cvalve = db.session.query(Valve).filter_by(crop_id=crop.id).first()


            # Check if there's irrigation data for the crop
            if irrigation_data_query:
                print(f"##### Irrigation Needs for {crop.name} #####")
                for data in irrigation_data_query:
                    print(f"Bulletin ID: {data.bulletin}, Irrigation Need: {data.irrigation_need}, "
                          f"Irrigation Number: {data.irrigation_number}, "
                          f"Irrigation Dose: {data.irrigation_dose}")

                # Check if there's already an entry for the current week in irrigationData
                existing_entry = db.session.query(irrigationData).filter(
                    irrigationData.crop_id == crop.id,
                    irrigationData.start_date == start_of_week,
                    irrigationData.end_date == end_of_week
                ).first()
                

                 
                if not existing_entry:
                    # Create a new irrigation_data entry
                    for data in irrigation_data_query:
                        new_irrigation_entry = irrigationData(
                            crop_id=crop.id,
                            start_date=start_of_week,
                            end_date=end_of_week,
                            counter_start_date_data = cvalve.counter,
                            counter_end_date_data = 0,
                            required_quantity=data.irrigation_need*crop.crop_size,  # Assuming this is what you want to set
                            supplied_quantity=0
                        )
                        db.session.add(new_irrigation_entry)
                        print(f"Added irrigation data for {crop.name}: Required Quantity = {data.irrigation_need}")
                        db.session.commit()

                    ##reset the counter of the valve
                ##################### water phase ############
                
                   # Get all crops
        crops = db.session.query(Crop).all()

     #      for crop in crops:
     #          print(f"Processing crop: {crop.name}")
        all_irrigation_data = db.session.query(irrigationData).all()
        print("all data")
        print(all_irrigation_data) 
            ###watering actually
        for irrigation in all_irrigation_data:
            print("irigation")
            # Iterate over each crop and take action.
            if (irrigation.supplied_quantity < irrigation.required_quantity):
                print(f"Watering Crop {crop.name}")
                valve = db.session.query(Valve).filter(Valve.crop_id == irrigation.crop_id).first()
                valve_url = valve.hwaddr  # Copy hwaddr to valve_url
                # Find the corresponding valve for the crop
                valve = db.session.query(Valve).filter(Valve.crop_id == irrigation.crop_id).first()
                if valve:
                    valve.status = True  # Set status to True
                    print(f"Valve for Crop ID {irrigation.crop_id} activated. hwaddr: {valve_url}")
                    valve_url = valve.hwaddr  # Copy hwaddr to valve_url
                    ###handle the websocket here. to-do.

                    valve.counter += units_per_minute ## watering within a minute time. 
                    irrigation.supplied_quantity +=units_per_minute
                    
                    
                     # Commit the changes for the valve status updates
                    db.session.commit()    
            else:
                ###handle websocket close-to-do.
                valve = db.session.query(Valve).filter(Valve.crop_id == irrigation.crop_id).first()
                valve_url = valve.hwaddr  # Copy hwaddr to valve_url
                if(valve.status == 1):
                    print(f"Valve for Crop ID {irrigation.crop_id} closed. hwaddr: {valve_url}")
                    valve.status = 0
                    irrigation.counter_end_date_data = valve.counter

                    db.session.commit()

    # Commit the session after processing all crops
        print("precom")
        db.session.commit()
        print("afcom")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.session.rollback()
    finally:
        db.session.close()
