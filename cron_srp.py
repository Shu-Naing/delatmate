from flask import Blueprint, render_template, flash, request, redirect, url_for
import os
from flask_login import login_required, current_user
from models import Mocdm_erp,Mocdm_pending,Mocdm_consumption,Mocdm_schedule
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import logging
from __init__ import create_app, db

cron_srp = Blueprint('cron_srp', __name__)

@cron_srp.route('/deleteWithTime', methods = ['GET', 'POST'])
def deleteWithTime():
    try:
        one_years_ago = datetime.now().replace(year=datetime.now().year-1, month=1, day=1)
        Mocdm_erp.query.filter(Mocdm_erp.vessel_date < one_years_ago).delete()
        Mocdm_pending.query.filter(Mocdm_pending.vessel_date < one_years_ago).delete()
        Mocdm_consumption.query.filter(Mocdm_consumption.date < one_years_ago).delete()
        db.session.commit()
        x = logging.basicConfig(filename= f'delete_data.log', level=logging.ERROR)
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return 'OK'
