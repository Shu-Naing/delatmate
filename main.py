from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask import Flask, session
import os
from flask_login import login_required, current_user
from models import Mocdm_erp,Mocdm_pending,Mocdm_consumption,Mocdm_schedule
# from flask_crontab import Crontab
from __init__ import create_app, db

main = Blueprint('main', __name__)
# crontab = Crontab(main)

def is_active(page):
    return True if request.path == page else False

@main.route('/imageupload', methods=['POST'])
def imageupload():
    file = request.files['image']
    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    id = request.form.get('id')
    image = Mocdm_schedule.query.filter_by(id=id).first()
    image.image_path = file_path
    db.session.commit()
    return redirect(url_for('auth.schedulelist'))

@main.route('/') 
def index():
    if not 'user_session' in session:
        return render_template('login.html')
    else:
        return redirect(url_for('main.profile'))

@main.route('/erpfileupload') 
def erpfileupload():
    return render_template('erpfileupload.html')

@main.route('/sheduleupload') 
def sheduleupload():
    return render_template('schedulereportupload.html')

@main.route('/pendingfileupload') 
def pendingfileupload():
    return render_template('pendingfileupload.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name,  home_active=is_active('/profile'))

@main.route('/edit')
@login_required
def edit():
    return render_template('edit.html', name=current_user.name)

@main.route('/employee')
@login_required
def employee():
    return render_template('employee.html', name=current_user.name)
    
app = create_app() 
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # app.run(host='150.95.26.122', debug=False) 
    app.run(debug=True) 