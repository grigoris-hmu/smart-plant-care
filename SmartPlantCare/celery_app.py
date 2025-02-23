from celery import Celery
from datetime import timedelta
import SmartPlantCare.celery.tasks

###########################
##CELERY CONFIGURATION ####
###########################
def make_celery(app):

    CELERY_TIMEDELTA = int(app.config['CELERY_TIMEDELTA'])
    print ("##### CELERY TIMEDELTA #####")
    print(CELERY_TIMEDELTA)
    result_backend = app.config['RESULT_BACKEND']
    print ("##### CELERY RESULT_BACKEND #####")
    print(result_backend)
    broker_url = app.config['BROKER']
    print ("##### CELERY BROKER #####")
    print(broker_url)
    celery = Celery(
        app.import_name,
        backend = result_backend,
        broker = broker_url
    )
    celery.conf.update(app.config)
    # Enable task events
    celery.conf.update(
        CELERYD_TASK_EVENTS=True,
        timezone='UTC',
        enable_utc=True,
    )
    
    # Registering the periodic tasks(our Celery-beat schedule)
    celery.conf.beat_schedule = {
        'check-crop-thresholds-every-minute': {
            'task': 'SmartPlantCare.celery.tasks.check_sensor_data_thresholds',
            'schedule': timedelta(seconds=CELERY_TIMEDELTA),  # (frequency of task)
        },
    }

    # Registering the periodic tasks(our Celery-beat schedule) -- watering execution
    celery.conf.beat_schedule = {
        'check-crop-watering-every-minute': {
            'task': 'SmartPlantCare.celery.tasks.check_watering',
            'schedule': timedelta(seconds=60),  # (frequency of task)
        },
    }



    # Enable Flask's app context in tasks
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
