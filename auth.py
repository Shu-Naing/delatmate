from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask import Flask, request
from werkzeug.security import generate_password_hash, check_password_hash
from models import Mocdm_users,Mocdm_erp,Mocdm_pending,Mocdm_consumption,Mocdm_schedule
from os.path import join, dirname, realpath
from flask import Flask, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_security import roles_accepted
from io import TextIOWrapper
from flask import make_response
from sqlalchemy import exc
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from flask import Flask, send_file
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pyttsx3 
import csv
import logging
import traceback
import sys
import os
import pandas as pd
import xlsxwriter
import io
from __init__ import db

auth = Blueprint('auth', __name__) 

@auth.route('/login', methods=['GET', 'POST']) 
def login():
    try:
        if request.method=='GET': 
            return render_template('login.html')
        else: 
            name = request.form.get('name')
            password = request.form.get('password')
            remember = True if request.form.get('remember') else False
            user = Mocdm_users.query.filter_by(name=name).first()
            session["role"] = user.role
            if not user:
                flash('Please sign up before!')
                return redirect(url_for('auth.signup'))
            elif not check_password_hash(user.password, password):
                flash('Please check your login details and try again.')
                return redirect(url_for('auth.login')) 
            login_user(user, remember=remember)
            return redirect(url_for('main.profile'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.profile')) 

@auth.route('/logout') 
@login_required
def logout(): 
    logout_user()
    return redirect(url_for('main.index'))
    
@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    try:
        if request.method == 'POST':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            
            user = Mocdm_users.query.get(current_user.id)        
            if check_password_hash(user.password, current_password):
                hashed_password = generate_password_hash(new_password)
                user.password = hashed_password
                db.session.commit()
                return redirect(url_for('auth.emplist'))
            else:
                flash('Incorrect password')
        
        return redirect(url_for('auth.emplist'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.emplist')) 

@auth.route('/signup', methods=['GET', 'POST'])
# @login_required
def signup():
    try:
        if request.method=='GET': 
            return render_template('signup.html')
        else:
            email = request.form.get('email')
            name = request.form.get('name')
            phone = request.form.get('phone')
            password = request.form.get('password')
            role = request.form.get('role')
            user = Mocdm_users.query.filter_by(email=email).first()
            if user: 
                flash('Email address already exists')
                return redirect(url_for('auth.signup'))
            new_user = Mocdm_users(email=email, name=name,phone=phone, password=generate_password_hash(password, method='sha256'),role=role) 
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('auth.login'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.erplist')) 

@auth.route('/updateEmp', methods=['GET', 'POST'])
@login_required
def updateEmp():
    try:
        if request.method == 'POST':
            got_data = Mocdm_users.query.get(request.form.get('id'))
            got_data.name = request.form['name']
            got_data.email = request.form['email']
            got_data.phone = request.form['phone']
            db.session.commit()
            return redirect(url_for('auth.emplist'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.emplist'))  

@auth.route('/emplist', defaults={'page_num':1})
@auth.route('/emplist/<int:page_num>')
@login_required
def emplist(page_num):
    try:
        if request.method=='GET':
            all_data = Mocdm_users.query.paginate(per_page=5, page=page_num, error_out=True)
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return render_template('employee.html',all_data = all_data) 

@auth.route("/erpupload", methods=['POST'])
@login_required
def erpupload():
    try:
        if request.method == 'POST':
            excel_file = request.files['file']
            col_names = ['PO','款号','款号版本', '产品编号', '产品名称' , '产品主色','产品配色','货期','配色项目','物料分类','物料编号','物料英文名称','物料名称','规格','颜色','库存单位用量','库存单位','生产损耗','生产用量','订单数量','需求总用量','备注']
            df = pd.read_excel(excel_file,names=col_names,header = None,skiprows=1)
            df = df.fillna('')
            for i,row in df.iterrows():
                txt = row['产品编号']
                x = txt.split('-')
                if len(x) < 2:
                    y = x[0]
                else:
                    y = x[0]+x[1]
                all_data = Mocdm_erp(po=row['PO'],style=row['款号'],buyer_version=row['款号版本'],buyer=row['产品编号'],product_name=row['产品名称'],main_color=row['产品主色'],season=row['产品配色'],vessel_date=row['货期'],category=row['配色项目'],material_classification=row['物料分类'],material_code=row['物料编号'],material=row['物料英文名称'],material_chinese=row['物料名称'],size=row['规格'],color=row['颜色'],org_consume=row['库存单位用量'],unit=row['库存单位'],loss=row['生产损耗'],consume_point=row['生产用量'],order_qty=row['订单数量'],consume=row['需求总用量'],gp=row['备注'],pending_buyer=y)
                db.session.add(all_data)
                db.session.commit()
            return redirect(url_for('auth.erplist'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.erplist'))
    
@auth.route('/erplist', defaults={'page_num':1})
@auth.route('/erplist/<int:page_num>', methods=['GET', 'POST'])
@login_required
def erplist(page_num):
    if request.method=='GET':
        all_data = Mocdm_erp.query.paginate(per_page=100, page=page_num, error_out=True)
        return render_template('erp.html',all_data = all_data)

@auth.route('/erpUpdate', methods=['GET', 'POST'])
@login_required
def erpUpdate():
    try:
        if request.method=='POST':
            all_data = Mocdm_erp.query.get(request.form.get('id'))
            all_data.buyer_version = request.form['buyer_version']
            all_data.product_name = request.form['product_name']
            all_data.main_color = request.form['main_color']
            all_data.category = request.form['category']
            all_data.material_classification = request.form['material_classification']
            all_data.material_code = request.form['material_code']
            all_data.material = request.form['material']
            all_data.material_chinese = request.form['material_chinese']
            all_data.size = request.form['size']
            all_data.org_consume = request.form['org_consume']
            all_data.unit = request.form['unit']
            all_data.loss = request.form['loss']
            all_data.consume_point = request.form['consume_point']
            all_data.order_qty = request.form['order_qty']
            all_data.consume = request.form['consume']
            db.session.commit()
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.erplist'))

@auth.route('/searcherp', methods=['GET','POST'])
@login_required
def searcherp():
    try:
        if request.method=='POST':
            po = request.form['po']
            style = request.form['style']
            buyer = request.form['buyer']
            color = request.form['color']
            gp = request.form['gp']
            search1 = "%{}%".format(po)
            search2 = "%{}%".format(style)
            search3 = "%{}%".format(buyer)
            search4 = "%{}%".format(color)
            search5 = "%{}%".format(gp)
            all_data = Mocdm_erp.query.filter((Mocdm_erp.po.like(search1)),(Mocdm_erp.style.like(search2)),(Mocdm_erp.buyer.like(search3)),(Mocdm_erp.color.like(search4)),(Mocdm_erp.gp.like(search5))).all()
            return render_template("searcherp.html",po = po, all_data = all_data)
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return render_template("searchpending.html", po = po, all_data = all_data)


@auth.route('/searchpending', methods=['GET','POST'])
@login_required
def searchpending():
    try:
        if request.method=='POST':
            po = request.form['po']
            style = request.form['style']
            org_buyer = request.form['org_buyer']
            color = request.form['color']
            gp_name = request.form['gp_name']
            ext_dely = request.form['ext_dely']
            order_date = request.form['order_date']
            search1 = "%{}%".format(po)
            search2 = "%{}%".format(style)
            search3 = "%{}%".format(org_buyer)
            search4 = "%{}%".format(color)
            search5 = "%{}%".format(gp_name)
            search6 = "%{}%".format(ext_dely)
            search7 = "%{}%".format(order_date)
            all_data = Mocdm_pending.query.filter((Mocdm_pending.po.like(search1)),(Mocdm_pending.style.like(search2)),(Mocdm_pending.org_buyer.like(search3)),(Mocdm_pending.color.like(search4)),(Mocdm_pending.gp_name.like(search5)),(Mocdm_pending.ext_dely.like(search6)),(Mocdm_pending.order_date.like(search7))).all()
            return render_template("searchpending.html", po = po, all_data = all_data)
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return render_template("searchpending.html", po = po, all_data = all_data)

@auth.route('/pendingUpdate', methods=['GET', 'POST'])
@login_required
def pendingUpdate():
    if request.method=='POST':
        all_data = Mocdm_pending.query.get(request.form.get('id'))
        all_data.mcn = request.form['mcn']
        all_data.ship_to = request.form['ship_to']
        all_data.label = request.form['label']
        all_data.linked_store = request.form['linked_store']
        all_data.des = request.form['des']
        all_data.qty = request.form['qty']
        all_data.factory = request.form['factory']
        all_data.db_gb_code = request.form['db_gb_code']
        all_data.upc_no = request.form['upc_no']
        all_data.linked_so_no = request.form['linked_so_no']
        all_data.ref_no = request.form['linked_so_no']
        all_data.linked_so_no = request.form['ref_no']
        all_data.material_log_no = request.form['material_log_no']
        all_data.season = request.form['season']
        all_data.kmz_id = request.form['kmz_id']
        all_data.remark = request.form['remark']
        all_data.shpg_job = request.form['shpg_job']
        all_data.status = request.form['status']
        db.session.commit()
        return redirect(url_for('auth.pendinglist'))

@auth.route("/pending_upload", methods=['POST'])
@login_required
def pending_upload():
    try:
        if request.method == 'POST':
            excel_file = request.files['file']
            col_names = ['Ex-Fty','MCN','PO#', 'Ship To', 'Label' , 'Linked Store','DES','Group Name','Style#','Buyer#','COLOUR','QTY','Vessel','Factory','DB/GB Pkg Code','SDN PO','Customer Po#','UPC Number','Linked SO Num','Ref.Number','Material Lot No:','Season','Buyer','Order Date','KZM ID','Remark','ShpgJob','xFty Date']
            df = pd.read_excel(excel_file,names=col_names,header = None,skiprows=1)
            df = df.fillna('')
            for i,row in df.iterrows():
                txt = 'MYANMAR'
                all_data = Mocdm_pending(ext_dely=row['Ex-Fty'],mcn=row['MCN'],po=row['PO#'],ship_to=row['Ship To'],label=row['Label'],linked_store=row['Linked Store'],des=row['DES'],gp_name=row['Group Name'],style=row['Style#'],org_buyer=row['Buyer#'],color=row['COLOUR'],qty=row['QTY'],vessel_date=row['Vessel'],factory=row['Factory'],db_gb_code=row['DB/GB Pkg Code'],sdn_po=row['SDN PO'],customer_po=row['Customer Po#'],upc_no=row['UPC Number'],linked_so_no=row['Linked SO Num'],ref_no=row['Ref.Number'],material_log_no=row['Material Lot No:'],season=row['Season'],buyer_txt=row['Buyer'],order_date=row['Order Date'],kmz_id=row['KZM ID'],remark=row['Remark'],shpg_job=row['ShpgJob'],xfty_date=row['xFty Date'],myanmar=txt,previous=row['Ex-Fty'])
                print(all_data)
                db.session.add(all_data)
                db.session.commit()
            return redirect(url_for('auth.pendinglist'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.pendinglist'))

@auth.route('/pendinglist', defaults={'page_num':1})
@auth.route('/pendinglist/<int:page_num>', methods=['GET','POST'])
@login_required
def pendinglist(page_num):
    if request.method=='GET':
        all_data = Mocdm_pending.query.paginate(per_page=100, page=page_num, error_out=True)
        return render_template('pending.html',all_data = all_data)

@auth.route('/deletePending', methods=['POST'])
def deletePending():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    
    all_data = Mocdm_pending.query.filter(Mocdm_pending.ext_dely >= start_datetime, Mocdm_pending.ext_dely <= end_datetime).delete()
    db.session.commit()
    return redirect(url_for('auth.pendinglist'))

@auth.route('/orderlist', defaults={'page_num':1})
@auth.route('/orderlist/<int:page_num>', methods=['GET','POST'])
@login_required
def orderlist(page_num):
    if request.method=='GET':
        all_data = db.session.query(Mocdm_erp.id,Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).paginate(per_page=1000, page=page_num, error_out=True) 
        return render_template('orderlist.html',all_data = all_data)

@auth.route('/download/orderlist', methods=['GET', 'POST'])
def download_report():
    all_data = db.session.query(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).all()
    # all_data = db.session.query(Mocdm_erp.id,Mocdm_erp.po,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.buyer,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp).all()
    df = pd.DataFrame((tuple(t) for t in all_data), columns=('PO#','LABEL','DES','D/C','PREVIOUS','DELY','MYANMAR','STYLE','BUYER VERSION','BUYER','PRODUCT NAME','MAIN COLOR','SEASON','VESSEL DATE','CATEGORY','MATERIAL CLASSIFICATION','MATERIAL CODE','MATERIAL NAME IN CHINESE','MATERIAL','SIZE','COLOUR','ORIGINAL CONSUME','UNIT','LOSS','CONSUME POINT','ORDER QTY','CONSUME','GROUP','ORDER DATE','FACTORY'))                                  
    # df = pd.DataFrame((tuple(t) for t in all_data), columns=('id','po','style','buyer_version','buyer','product_name','main_color','season','vessel_date','category','material_classification','material_code','material','material_chinese','size','color','org_consume','unit','loss','consume_point','order_qty','consume','gp','pending_buyer'))
    out = io.BytesIO()
    writer = pd.ExcelWriter(out, engine='xlsxwriter')
    df.to_excel(excel_writer=writer, index=False, sheet_name='Sheet1')
    writer.save()
    writer.close()
    r = make_response(out.getvalue())
    r.headers["Content-Disposition"] = "attachment; filename=combination.xlsx"
    r.headers["Content-type"] = "application/x-xls"

    return r

# @auth.route('/export')
# def export():
#     data = db.session.query(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).all()

#     # Convert SQLAlchemy query results to a pandas DataFrame
#     # df = pd.read_sql(data.statement, db.session.bind)
#     df = pd.DataFrame((list(t) for t in data), columns=('PO#','LABEL','DES','D/C','PREVIOUS','DELY','MYANMAR','STYLE','BUYER VERSION','BUYER','PRODUCT NAME','MAIN COLOR','SEASON','VESSEL DATE','CATEGORY','MATERIAL CLASSIFICATION','MATERIAL CODE','MATERIAL NAME IN CHINESE','SIZE','COLOUR','ORIGINAL','CONSUME','UNIT','LOSS','CONSUME POINT','ORDER QTY','CONSUME','GROUP','ORDER DATE','FACTORY'))


#     # Create a response object with the Excel file
#     r = make_response(df.to_excel('users.xlsx', index=False))
#     r.headers['Content-Type'] = 'application/x-xls'
#     r.headers['Content-Disposition'] = 'attachment; filename=users.xlsx'

#     return r

@auth.route('/download')
def download_excel():
    file_name = generate_excel()
    return send_file(file_name, attachment_filename=file_name, as_attachment=True)

def generate_excel():
    data = db.session.query(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).all()
    df = pd.DataFrame([(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory) for d in data], columns=['PO#','LABEL','DES','D/C','PREVIOUS','DELY','MYANMAR','STYLE','BUYER VERSION','BUYER','PRODUCT NAME','MAIN COLOR','SEASON','VESSEL DATE','CATEGORY','MATERIAL CLASSIFICATION','MATERIAL CODE','MATERIAL NAME IN CHINESE','SIZE','COLOUR','ORIGINAL','CONSUME','UNIT','LOSS','CONSUME POINT','ORDER QTY','CONSUME','GROUP','ORDER DATE','FACTORY'])
    file_name = 'data.xlsx'
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Data')
    writer.save()
    return file_name

@auth.route('/searchorderlist', methods=['GET','POST'])
@login_required
def searchorderlist():
    if request.method=='POST':
        po = request.form['po']
        style = request.form['style']
        org_buyer = request.form['org_buyer']
        color = request.form['color']
        gp_name = request.form['gp_name']
        ext_dely = request.form['ext_dely']
        order_date = request.form['order_date']
        factory = request.form['factory']
        label = request.form['label']
        search1 = "%{}%".format(po)
        search2 = "%{}%".format(style)
        search3 = "%{}%".format(org_buyer)
        search4 = "%{}%".format(color)
        search5 = "%{}%".format(gp_name)
        search6 = "%{}%".format(ext_dely)
        search7 = "%{}%".format(order_date)
        search8 = "%{}%".format(factory)
        search9 = "%{}%".format(label)
        all_data = db.session.query(
        Mocdm_erp.po,
        Mocdm_pending.label,
        Mocdm_pending.des,
        Mocdm_pending.mcn,
        Mocdm_pending.previous,
        Mocdm_pending.ext_dely,
        Mocdm_pending.myanmar,
        Mocdm_erp.style,
        Mocdm_erp.buyer_version,
        Mocdm_erp.pending_buyer,
        Mocdm_erp.product_name,
        Mocdm_erp.main_color,
        Mocdm_erp.season,
        Mocdm_erp.vessel_date,
        Mocdm_erp.category,
        Mocdm_erp.material_classification,
        Mocdm_erp.material_code,
        Mocdm_erp.material,
        Mocdm_erp.material_chinese,
        Mocdm_erp.size,
        Mocdm_erp.color,
        Mocdm_erp.org_consume,
        Mocdm_erp.unit,
        Mocdm_erp.loss,
        Mocdm_erp.consume_point,
        Mocdm_erp.order_qty,
        Mocdm_erp.consume,
        Mocdm_erp.gp,
        Mocdm_pending.order_date,
        Mocdm_pending.factory).join(Mocdm_pending,
        (Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.color == Mocdm_erp.color) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.org_buyer == Mocdm_erp.buyer),
        isouter = True).filter((Mocdm_pending.po.like(search1)),(Mocdm_pending.style.like(search2)),(Mocdm_pending.org_buyer.like(search3)),(Mocdm_pending.color.like(search4)),(Mocdm_pending.gp_name.like(search5)),(Mocdm_pending.ext_dely.like(search6)),(Mocdm_pending.order_date.like(search7))).all()   
        if not all_data:
            return render_template("orderlist.html", po = po)
        else:
            return render_template("orderlistSearch.html", po = po, all_data = all_data)

@auth.route('/consumptionreport', methods=['GET','POST'])
@login_required
def consumptionreport():
    if request.method=='GET':
        style = request.args.get('style')
        group_name = request.args.get('group_name')
        qty_no = request.args.get('qty_no')
        dely_date = request.args.get('dely_date')
        buyer = request.args.get('buyer')
        all_data = db.session.query(Mocdm_erp.id.label("erpid"),Mocdm_consumption.id,Mocdm_erp.category,Mocdm_erp.material,Mocdm_erp.color,Mocdm_erp.unit,Mocdm_erp.consume,Mocdm_erp.order_qty,Mocdm_consumption.issued_qty,Mocdm_consumption.balance,Mocdm_consumption.date,Mocdm_consumption.issued_by_leader,Mocdm_consumption.factory_line,Mocdm_consumption.reciever,Mocdm_consumption.remark).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.color == Mocdm_erp.color) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.org_buyer == Mocdm_erp.buyer),isouter = True).join(Mocdm_consumption,(Mocdm_consumption.erp_id == Mocdm_erp.id),isouter = True).filter(Mocdm_pending.gp_name == group_name,Mocdm_pending.style == style,Mocdm_pending.qty == qty_no,Mocdm_pending.ext_dely == dely_date).all()      
        return render_template('consumptionreport.html',all_data = all_data, style=style, group_name=group_name, qty_no=qty_no, dely_date=dely_date, buyer=buyer)


@auth.route('/searchcreport', methods=['GET','POST'])
@login_required
def searchcreport():
    if request.method=='POST':
        ext_dely = request.form['ext_dely']
        qty = request.form['qty']
        gp_name = request.form['gp_name']
        style = request.form['style']
        search1 = "%{}%".format(ext_dely)
        search2 = "%{}%".format(qty)
        search3 = "%{}%".format(gp_name)
        search4 = "%{}%".format(style)
        all_data = Mocdm_pending.query.filter((Mocdm_pending.ext_dely.like(search1)),(Mocdm_pending.qty.like(search2)),(Mocdm_pending.gp_name.like(search3)),(Mocdm_pending.style.like(search4))).all()
        if not all_data:
            return "no data"
        else:
            return render_template("searchpending.html", all_data = all_data)


@auth.route('/consumptionreportUpdate', methods=['GET', 'POST'])
@login_required
def consumptionreportUpdate():
    if request.method=='POST':
        data = Mocdm_consumption.query.get(request.form.get('id'))
        if data:
            all_data = Mocdm_consumption(id=request.form['id'],issued_qty=request.form['issued_qty'],balance=request.form['balance'],date=request.form['date'],issued_by_leader=request.form['issued_by_leader'],factory_line=request.form['factory_line'],reciever=request.form['reciever'],remark=request.form['remark'])
            db.session.merge(all_data)
            db.session.commit()
            return redirect(url_for('auth.consumptionreport'))
        else:
            all_data = Mocdm_consumption(erp_id=request.form['erpid'],issued_qty=request.form['issued_qty'],balance=request.form['balance'],date=request.form['date'],issued_by_leader=request.form['issued_by_leader'],factory_line=request.form['factory_line'],reciever=request.form['reciever'],remark=request.form['remark'])
            db.session.add(all_data)
            db.session.commit()
            return redirect(url_for('auth.consumptionreport'))        
            

@auth.route('/download/consumptionreport', methods=['GET', 'POST'])
def download_consumptionreportreport():
    all_data = db.session.query(Mocdm_erp.id.label("erpid"),Mocdm_consumption.id,Mocdm_erp.category,Mocdm_erp.material,Mocdm_erp.color,Mocdm_erp.unit,Mocdm_erp.consume,Mocdm_erp.order_qty,Mocdm_consumption.issued_qty,Mocdm_consumption.balance,Mocdm_consumption.date,Mocdm_consumption.issued_by_leader,Mocdm_consumption.factory_line,Mocdm_consumption.reciever,Mocdm_consumption.remark).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.color == Mocdm_erp.color) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.org_buyer == Mocdm_erp.buyer),isouter = True).join(Mocdm_consumption,(Mocdm_consumption.erp_id == Mocdm_erp.id),isouter = True).filter(Mocdm_pending.gp_name == 'VIKKY',Mocdm_pending.style == 'SDN-926B',Mocdm_pending.ext_dely == '2022-01-23').all()      
    df = pd.DataFrame((tuple(t) for t in all_data), columns=('CATEGORY','MATERIAL','COLOUR','UNIT','CONSUME','ORDER QTY','ISSUED QTY','BALANCE','DATE','ISSUED BY (Leader)','Factory line','RECEIVER','REMARK'))
    out = io.BytesIO()
    writer = pd.ExcelWriter(out, engine='openpyxl')
    df.to_excel(excel_writer=writer, index=False, sheet_name='Sheet1')
    writer.save()
    writer.close()
    r = make_response(out.getvalue())
    r.headers["Content-Disposition"] = "attachment; filename=consumptionreport.xlsx"
    r.headers["Content-type"] = "application/x-xls"

    return r

@auth.route("/scheduleUpload", methods=['POST'])
@login_required
def scheduleUpload():
    try:
        if request.method == 'POST':
            excel_file = request.files['file']
            col_names = ['LINE','DELY','QTY','Target(H/W)','Balance(PVC)', 'Zip & Thread' , 'Group','Style','Version','Buyer']
            df = pd.read_excel(excel_file,names=col_names,header = None,skiprows=1)
            df = df.fillna('')
            for i,row in df.iterrows():
                all_data = Mocdm_schedule(line=row['LINE'],dely=row['DELY'],qty=row['QTY'],target=row['Target(H/W)'],balance=row['Balance(PVC)'],zip_thread=row['Zip & Thread'],group=row['Group'],style=row['Style'],version=row['Version'],buyer=row['Buyer'])
                db.session.add(all_data)
                db.session.commit()
            return redirect(url_for('auth.schedulelist'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.schedulelist'))
        

@auth.route('/schedulelist', defaults={'page_num':1})
@auth.route('/schedulelist/<int:page_num>', methods=['GET', 'POST'])
@login_required
def schedulelist(page_num):
    if request.method=='GET':
        all_data = Mocdm_schedule.query.paginate(per_page=100, page=page_num, error_out=True)
        return render_template('schedulereport.html',all_data = all_data)

@auth.route('/deleteSchedule/<id>/', methods = ['GET', 'POST'])
def deleteSchedule(id):
    all_data = Mocdm_schedule.query.get(id)
    db.session.delete(all_data)
    db.session.commit()
    return redirect(url_for('auth.schedulelist'))

@auth.route('/image/<int:id>')
def view_image(id):
    image = Mocdm_schedule.query.filter_by(id=id).first()
    return render_template('schedulereport.html', image=image)

@auth.route('/deleteWithTime')
def deleteWithTime():
    two_years_ago = datetime.now().replace(year=datetime.now().year-2, month=1, day=1)
    Mocdm_erp.query.filter(Mocdm_erp.created_date < two_years_ago).delete()
    Mocdm_pending.query.filter(Mocdm_pending.created_date < two_years_ago).delete()
    Mocdm_consumption.query.filter(Mocdm_consumption.created_date < two_years_ago).delete()
    db.session.commit()
    return ''