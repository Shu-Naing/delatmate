from flask import Blueprint, render_template, redirect, url_for, request, flash, Response
from flask import Flask, request, jsonify
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
from datetime import timedelta
from flask import Flask, send_file
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import current_app
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from openpyxl.styles import Font
from io import BytesIO
import pyttsx3 
import csv
import logging
import traceback
import sys
import os
import pandas as pd
import xlsxwriter
import io
import re
from __init__ import db

auth = Blueprint('auth', __name__)


def is_active(page):
    return True if request.path == page else False

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
            if not user:
                flash('Please login agin!')
                return redirect(url_for('auth.login'))
            elif not check_password_hash(user.password, password):
                flash('Please check your login details and try again.')
                return redirect(url_for('auth.login')) 
            login_user(user, remember=remember)
            session["role"] = user.role
            current_page = current_app.config.get('CURRENT_PAGE')
            current_page_home = 'home'
            return redirect(url_for('main.profile'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('main.profile')) 

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
            id = request.form['id']
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            
            user = Mocdm_users.query.get(id)        
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
@login_required
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
            all_data = db.session.query(Mocdm_users).filter(~Mocdm_users.name.like('mocdev')).paginate(per_page=5, page=page_num, error_out=True)
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return render_template('employee.html',all_data = all_data, emp_active="is_active('/emp')") 

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
                if len(x) < 4:
                    y = x[1]
                else:
                    y = x[1]+x[2]
                c = row['款号']
                d = c.strip('')
                e = row['产品主色'] 
                f = e.upper()
                all_data = Mocdm_erp(po=row['PO'],style=d,buyer_version=row['款号版本'],buyer=row['产品编号'],product_name=row['产品名称'],main_color=f,season=row['产品配色'],vessel_date=row['货期'],category=row['配色项目'],material_classification=row['物料分类'],material_code=row['物料编号'],material=row['物料英文名称'],material_chinese=row['物料名称'],size=row['规格'],color=row['颜色'],org_consume=row['库存单位用量'],unit=row['库存单位'],loss=row['生产损耗'],consume_point=row['生产用量'],order_qty=row['订单数量'],consume=row['需求总用量'],gp=row['备注'],pending_buyer=y)
                db.session.add(all_data)
                db.session.commit()
            return redirect(url_for('auth.erplist'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.erplist'))
    
@auth.route('/erplist', defaults={'page_num':1}, methods=['GET', 'POST'])
@auth.route('/erplist/<int:page_num>', methods=['GET', 'POST'])
@login_required
def erplist(page_num):
    try:
        if request.method=='GET':
            po = request.args.get('po')
            style = request.args.get('style')
            gp = request.args.get('gp')
            main_color = request.args.get('main_color')
            buyer = request.args.get('buyer')
            all_data = Mocdm_erp.query.paginate(per_page=100, page=page_num, error_out=True)
            return render_template('erp.html',po = po,gp=gp,style=style,buyer=buyer,main_color=main_color,all_data = all_data, erp_active="is_active('/erp')")
        else:
            po = request.form['po']
            style = request.form['style']
            buyer = request.form['buyer']
            main_color = request.form['main_color']
            gp = request.form['gp']
            session['po'] = po
            session['style'] = style
            session['buyer'] = buyer
            session['main_color'] = main_color
            session['gp'] = gp
            search1 = "%{}%".format(po)
            search2 = "%{}%".format(style)
            search3 = "%{}%".format(buyer)
            search4 = "%{}%".format(main_color)
            search5 = "%{}%".format(gp)
            all_data = Mocdm_erp.query.filter((Mocdm_erp.po.like(search1)),(Mocdm_erp.style.like(search2)),(Mocdm_erp.buyer.like(search3)),(Mocdm_erp.main_color.like(search4)),(Mocdm_erp.gp.like(search5))).paginate(per_page=100, page=page_num, error_out=True)
            return render_template("erp.html",po = po,gp=gp,buyer=buyer,main_color=main_color, all_data = all_data, erp_active="is_active('/erp')")
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return render_template('erp.html',po = po,gp=gp,style=style,buyer=buyer,main_color=main_color,all_data = all_data, erp_active="is_active('/erp')")
    

@auth.route('/download_erp', methods=['GET', 'POST'])
def download_erp():
    if request.args.get('search') == 'true':
        po = request.args.get('po')
        style = request.args.get('style')
        buyer = request.args.get('buyer')
        main_color = request.args.get('main_color')
        gp = request.args.get('gp')
        po = "%{}%".format(po)
        style = "%{}%".format(style)
        buyer = "%{}%".format(buyer)
        main_color = "%{}%".format(main_color)
        gp = "%{}%".format(gp)
        all_data = Mocdm_erp.query.filter((Mocdm_erp.po.like(po)),(Mocdm_erp.style.like(style)),(Mocdm_erp.buyer.like(buyer)),(Mocdm_erp.color.like(main_color)),(Mocdm_erp.gp.like(gp))).all()
        wb = Workbook()
        ws = wb.active
        ws.append(['PO','STYLE','BUYER VERSION','BUYER','PRODUCT NAME','MAIN COLOR','SEASON','VESSEL DATE','CATEGORY','MATERIAL CLASSIFICATION','MATERIAL CODE','MATERIAL' ,'MATERIAL NAME IN CHINESE','SIZE','COLOUR','ORIGINAL CONSUME','UNIT','LOSS','CONSUME POINT','ORDER QTY','CONSUME','GROUP'])
        for item in all_data:
            ws.append([item.po,item.style,item.buyer_version,item.buyer,item.product_name,item.main_color,item.season,item.vessel_date.strftime('%d/%m/%Y'),item.category,item.material_classification,item.material_code,item.material,item.material_chinese,item.size,item.color,item.org_consume,item.unit,item.loss,item.consume_point,item.order_qty,item.consume,item.gp])
        file = BytesIO()
        wb.save(file)
        file.seek(0)
        filename = 'erp.xlsx'
        r = Response(
            file.read(),
            headers={
                'Content-Disposition': f'attachment;filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
        return r
    else:
        all_data1 = Mocdm_erp.query.all()
        wb = Workbook()
        ws = wb.active
        ws.append(['PO','STYLE','BUYER VERSION','BUYER','PRODUCT NAME','MAIN COLOR','SEASON','VESSEL DATE','CATEGORY','MATERIAL CLASSIFICATION','MATERIAL CODE','MATERIAL' ,'MATERIAL NAME IN CHINESE','SIZE','COLOUR','ORIGINAL CONSUME','UNIT','LOSS','CONSUME POINT','ORDER QTY','CONSUME','GROUP'])
        for item in all_data1:
            ws.append([item.po,item.style,item.buyer_version,item.buyer,item.product_name,item.main_color,item.season,item.vessel_date.strftime('%d/%m/%Y'),item.category,item.material_classification,item.material_code,item.material,item.material_chinese,item.size,item.color,item.org_consume,item.unit,item.loss,item.consume_point,item.order_qty,item.consume,item.gp])
        file = BytesIO()
        wb.save(file)
        file.seek(0)
        filename = 'erp.xlsx'
        r = Response(
            file.read(),
            headers={
                'Content-Disposition': f'attachment;filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
        return r
        

@auth.route('/erpUpdate', methods=['GET', 'POST'])
@login_required
def erpUpdate():
    try:
        if request.method=='POST':
            all_data = Mocdm_erp.query.get(request.form.get('id'))
            all_data.po = request.form['po']
            all_data.style = request.form['style']
            all_data.buyer = request.form['buyer']
            all_data.vessel_date = request.form['vessel_date']
            all_data.season = request.form['season']
            all_data.gp = request.form['gp']
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
            all_data.remark = request.form['remark']
            all_data.status = request.form['status']
            db.session.commit()
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return f"<td>{all_data.po}</td>,<td>{all_data.style}</td>,<td>{all_data.buyer_version}</td>,<td>{all_data.buyer}</td>,<td>{all_data.product_name}</td>,<td>{all_data.main_color}</td>,<td>{all_data.season}</td>,<td>{all_data.vessel_date}</td>,<td>{all_data.category}</td>,<td>{all_data.material_classification}</td>,<td>{all_data.material_code}</td>,<td>{all_data.material}</td>,<td>{all_data.material_chinese}</td>,<td>{all_data.size}</td>,<td>{all_data.color}</td>,<td>{all_data.org_consume}</td>,<td>{all_data.unit}</td>,<td>{all_data.loss}</td>,<td>{all_data.consume_point}</td>,<td>{all_data.order_qty}</td>,<td>{all_data.consume}</td>,<td>{all_data.gp}</td>,<td>{all_data.remark}</td>,<td>{all_data.status}</td>,<td><a href='/erpUpdate'  class='btn btn-primary' value='{all_data.id}' edit-row-value='{all_data.id}' data-bs-toggle='modal' data-bs-target='#myModal{all_data.id}'>Edit</a></td>"

@auth.route('/pendinglist', defaults={'page_num':1}, methods=['GET', 'POST'])
@auth.route('/pendinglist/<int:page_num>', methods=['GET','POST'])
@login_required
def pendinglist(page_num):
    if request.method=='GET':
        po = request.args.get('po')
        style = request.args.get('style')
        gp_name = request.args.get('gp_name')
        color = request.args.get('color')
        org_buyer = request.args.get('org_buyer')
        ext_dely = request.args.get('ext_dely')
        order_date = request.args.get('order_date')
        all_data = Mocdm_pending.query.paginate(per_page=100, page=page_num, error_out=True)
        return render_template('pending.html',po = po,style=style,org_buyer=org_buyer,color=color,gp_name=gp_name,ext_dely=ext_dely,order_date=order_date,all_data = all_data, pending_active="is_active('/pending')")
    else:
        po = request.form['po']
        style = request.form['style']
        org_buyer = request.form['org_buyer']
        color = request.form['color']
        gp_name = request.form['gp_name']
        ext_dely = request.form['ext_dely']
        order_date = request.form['order_date']
        session['po'] = po
        session['style'] = style
        session['org_buyer'] = org_buyer
        session['color'] = color
        session['gp_name'] = gp_name
        session['ext_dely'] = ext_dely
        session['order_date'] = order_date
        search1 = "%{}%".format(po)
        search2 = "%{}%".format(style)
        search3 = "%{}%".format(org_buyer)
        search4 = "%{}%".format(color)
        search5 = "%{}%".format(gp_name)
        search6 = "%{}%".format(ext_dely)
        search7 = "%{}%".format(order_date)
        all_data = Mocdm_pending.query.filter((Mocdm_pending.po.like(search1)),(Mocdm_pending.style.like(search2)),(Mocdm_pending.org_buyer.like(search3)),(Mocdm_pending.color.like(search4)),(Mocdm_pending.gp_name.like(search5)),(Mocdm_pending.ext_dely.like(search6)),(Mocdm_pending.order_date.like(search7))).paginate(per_page=100, page=page_num, error_out=True)
        return render_template("pending.html",po = po,style=style,org_buyer=org_buyer,color=color,gp_name=gp_name,ext_dely=ext_dely,order_date=order_date, all_data = all_data, pending_active="is_active('/pending')")

@auth.route('/download_pending', methods=['GET', 'POST'])
def download_pending():
    if request.args.get('search') == 'true':
        po = request.args.get('po')
        style = request.args.get('style')
        org_buyer = request.args.get('org_buyer')
        color = request.args.get('color')
        gp_name = request.args.get('gp_name')
        ext_dely = request.args.get('ext_dely')
        order_date = request.args.get('order_date')
        po = "%{}%".format(po)
        style = "%{}%".format(style)
        org_buyer = "%{}%".format(org_buyer)
        color = "%{}%".format(color)
        gp_name = "%{}%".format(gp_name)
        ext_dely = "%{}%".format(ext_dely)
        order_date = "%{}%".format(order_date)
        all_data = Mocdm_pending.query.filter((Mocdm_pending.po.like(po)),(Mocdm_pending.style.like(style)),(Mocdm_pending.org_buyer.like(org_buyer)),(Mocdm_pending.color.like(color)),(Mocdm_pending.gp_name.like(gp_name)),(Mocdm_pending.ext_dely.like(ext_dely)),(Mocdm_pending.order_date.like(order_date))).all()
        wb = Workbook()
        ws = wb.active
        ws.append(['EX - FTY ( DELY)','MCN ( D/C )','PO#','MYANMAR','Ship To','LABEL','Linked Store','DES','GROUP NAME','Style#','Buyer#','COLOUR','QTY','Vessel','Factory Name','DB/GB Pkg Code','SDN PO','Customer Po#','UPC Number','Linked SO Num',"Ref.Number",'Material Lot No:','Season','Buyer','ORDER DATE','KZM ID','Remark','ShpgJob','xFty Date','Status'])
        for item in all_data:
            ws.append([item.ext_dely,item.mcn,item.po,item.myanmar,item.ship_to,item.label,item.linked_store,item.des,item.gp_name,item.style,item.org_buyer,item.color,item.qty,item.vessel_date,item.factory,item.db_gb_code,item.sdn_po,item.customer_po,item.upc_no,item.linked_so_no,item.ref_no,item.material_log_no,item.season,item.buyer_txt,item.order_date,item.kmz_id,item.remark,item.shpg_job,item.xfty_date,item.status])
        file = BytesIO()
        wb.save(file)
        file.seek(0)
        filename = 'pending.xlsx'
        r = Response(
            file.read(),
            headers={
                'Content-Disposition': f'attachment;filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
        return r
    else:
        all_data1 = Mocdm_pending.query.all()
        wb = Workbook()
        ws = wb.active
        ws.append(['EX - FTY ( DELY)','MCN ( D/C )','PO#','MYANMAR','Ship To','LABEL','Linked Store','DES','GROUP NAME','Style#','Buyer#','COLOUR','QTY','Vessel','Factory Name','DB/GB Pkg Code','SDN PO','Customer Po#','UPC Number','Linked SO Num',"Ref.Number",'Material Lot No:','Season','Buyer','ORDER DATE','KZM ID','Remark','ShpgJob','xFty Date','Status'])
        for item in all_data1:
            ws.append([item.ext_dely,item.mcn,item.po,item.myanmar,item.ship_to,item.label,item.linked_store,item.des,item.gp_name,item.style,item.org_buyer,item.color,item.qty,item.vessel_date,item.factory,item.db_gb_code,item.sdn_po,item.customer_po,item.upc_no,item.linked_so_no,item.ref_no,item.material_log_no,item.season,item.buyer_txt,item.order_date,item.kmz_id,item.remark,item.shpg_job,item.xfty_date,item.status])
        file = BytesIO()
        wb.save(file)
        file.seek(0)
        filename = 'pending.xlsx'
        r = Response(
            file.read(),
            headers={
                'Content-Disposition': f'attachment;filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
        return r

@auth.route('/pendingUpdate', methods=['GET', 'POST'])
@login_required
def pendingUpdate():
    try:
        if request.method=='POST':
            all_data = Mocdm_pending.query.get(request.form.get('id'))
            all_data.ext_dely = request.form['ext_dely']
            all_data.po = request.form['po']
            all_data.myanmar = request.form['myanmar']
            all_data.gp_name = request.form['gp_name']
            all_data.style = request.form['style']
            all_data.color = request.form['color']
            all_data.vessel_date = request.form['vessel_date']
            all_data.customer_po = request.form['customer_po']
            all_data.buyer_txt = request.form['buyer_txt']
            all_data.order_date = request.form['order_date']
            all_data.xfty_date = request.form['xfty_date']
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
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    # return redirect(url_for('auth.pendinglist'))
    return f"<td>{all_data.ext_dely}</td>,<td>{all_data.mcn}</td>,<td>{all_data.po}</td>,<td>{all_data.myanmar}</td>,<td>{all_data.ship_to}</td>,<td>{all_data.label}</td>,<td>{all_data.linked_store}</td>,<td>{all_data.des}</td>,<td>{all_data.gp_name}</td>,<td>{all_data.style}</td>,<td>{all_data.org_buyer}</td>,<td>{all_data.color}</td>,<td>{all_data.qty}</td>,<td>{all_data.vessel_date}</td>,<td>{all_data.factory}</td>,<td>{all_data.db_gb_code}</td>,<td>{all_data.sdn_po}</td>,<td>{all_data.customer_po}</td>,<td>{all_data.upc_no}</td>,<td>{all_data.linked_so_no}</td>,<td>{all_data.ref_no}</td>,<td>{all_data.material_log_no}</td>,<td>{all_data.season}</td>,<td>{all_data.buyer_txt}</td>,<td>{all_data.order_date}</td>,<td>{all_data.kmz_id}</td>,<td>{all_data.remark}</td>,<td>{all_data.shpg_job}</td>,<td>{all_data.xfty_date}</td>,<td>{all_data.status}</td>,<td><a href='/pendingUpdate'  class='btn btn-primary' value='{all_data.id}' edit-row-value='{all_data.id}' data-bs-toggle='modal' data-bs-target='#myModal{all_data.id}'>Edit</a></td>"

@auth.route("/pending_upload", methods=['POST'])
@login_required
def pending_upload():
    try:
        if request.method == 'POST':
            excel_file = request.files['file']
            col_names = ['Ex-Fty','MCN','PO#', 'Ship To', 'Label' , 'Linked Store','DES','Group Name','Style#','Buyer#','COLOUR','QTY','Vessel','Factory','DB/GB Pkg Code','SDN PO','Customer Po#','UPC Number','Linked SO Num','Ref.Number','Material Lot No:','Season','Buyer','Order Date','KZM ID','Remark','ShpgJob','xFty Date']
            df = pd.read_excel(excel_file,names=col_names,header = None,skiprows=2)
            df = df.fillna('')
            for i,row in df.iterrows():
                txt = 'MYANMAR'
                x = row['Buyer#']
                h = x[:11]
                c = row['Style#']
                d = c.replace(" ", "")
                e = row['COLOUR']
                f = e.upper()
                trimmed_text = re.sub(r'^\s+|\s+$', '', f)
                all_data = Mocdm_pending(ext_dely=row['Ex-Fty'],mcn=row['MCN'],po=row['PO#'],ship_to=row['Ship To'],label=row['Label'],linked_store=row['Linked Store'],des=row['DES'],gp_name=row['Group Name'],style=d,org_buyer=h,color=trimmed_text,qty=row['QTY'],vessel_date=row['Vessel'],factory=row['Factory'],db_gb_code=row['DB/GB Pkg Code'],sdn_po=row['SDN PO'],customer_po=row['Customer Po#'],upc_no=row['UPC Number'],linked_so_no=row['Linked SO Num'],ref_no=row['Ref.Number'],material_log_no=row['Material Lot No:'],season=row['Season'],buyer_txt=row['Buyer'],order_date=row['Order Date'],kmz_id=row['KZM ID'],remark=row['Remark'],shpg_job=row['ShpgJob'],xfty_date=row['xFty Date'],myanmar=txt,previous=row['Ex-Fty'])
                db.session.add(all_data)
                db.session.commit()
            return redirect(url_for('auth.pendinglist'))
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.pendinglist'))

@auth.route('/deletePending', methods=['POST'])
def deletePending():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    
    all_data = Mocdm_pending.query.filter(Mocdm_pending.ext_dely >= start_datetime, Mocdm_pending.ext_dely <= end_datetime).delete()
    db.session.commit()
    return redirect(url_for('auth.pendinglist'))

@auth.route('/orderlist', defaults={'page_num':1}, methods=['GET','POST'])
@auth.route('/orderlist/<int:page_num>', methods=['GET','POST'])
@login_required
def orderlist(page_num):
    if request.method=='GET':
        po = request.args.get('po')
        style = request.args.get('style')
        org_buyer = request.args.get('org_buyer')
        color = request.args.get('color')
        gp_name = request.args.get('gp_name')
        ext_dely = request.args.get('ext_dely')
        order_date = request.args.get('order_date')
        factory = request.args.get('factory')
        label = request.args.get('label')
        all_data = db.session.query(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).paginate(per_page=100, page=page_num, error_out=True) 
        return render_template('orderlist.html', po = po,style = style, org_buyer = org_buyer, color = color, gp_name = gp_name, ext_dely = ext_dely, order_date = order_date, label=label, factory= factory,all_data = all_data, orderlist_active="is_active('/orderlist')")
    else:
        po = request.form['po']
        style = request.form['style']
        org_buyer = request.form['org_buyer']
        color = request.form['color']
        gp_name = request.form['gp_name']
        ext_dely = request.form['ext_dely']
        order_date = request.form['order_date']
        factory = request.form['factory']
        label = request.form['label']
        session['po'] = po
        session['style'] = style
        session['org_buyer'] = org_buyer
        session['color'] = color
        session['gp_name'] = gp_name
        session['ext_dely'] = ext_dely
        session['order_date'] = order_date
        session['factory'] = factory
        session['label'] = label
        search1 = "%{}%".format(po)
        search2 = "%{}%".format(style)
        search3 = "%{}%".format(org_buyer)
        search4 = "%{}%".format(color)
        search5 = "%{}%".format(gp_name)
        search6 = "%{}%".format(ext_dely)
        search7 = "%{}%".format(order_date)
        search8 = "%{}%".format(factory)
        search9 = "%{}%".format(label)
        all_data = db.session.query(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).filter((Mocdm_pending.po.like(search1)),(Mocdm_pending.style.like(search2)),(Mocdm_pending.org_buyer.like(search3)),(Mocdm_pending.color.like(search4)),(Mocdm_pending.gp_name.like(search5)),(Mocdm_pending.ext_dely.like(search6)),(Mocdm_pending.order_date.like(search7)),(Mocdm_pending.factory.like(search8)),(Mocdm_pending.label.like(search9))).paginate(per_page=100, page=page_num, error_out=True)
        return render_template("orderlist.html", po = po,style = style, org_buyer = org_buyer, color = color, gp_name = gp_name, ext_dely = ext_dely, order_date = order_date, factory= factory, label=label, all_data = all_data, orderlist_active="is_active('/orderlist')")

# all_data = db.session.query(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).all()

@auth.route('/download_order', methods=['GET', 'POST'])
def download_order():
    if request.args.get('search') == 'true':
        po = request.args.get('po')
        style = request.args.get('style')
        org_buyer = request.args.get('org_buyer')
        color = request.args.get('color')
        gp_name = request.args.get('gp_name')
        ext_dely = request.args.get('ext_dely')
        order_date = request.args.get('order_date')
        factory = request.args.get('factory')
        label = request.args.get('label')
        po = "%{}%".format(po)
        style = "%{}%".format(style)
        org_buyer = "%{}%".format(org_buyer)
        color = "%{}%".format(color)
        gp_name = "%{}%".format(gp_name)
        ext_dely = "%{}%".format(ext_dely)
        order_date = "%{}%".format(order_date)
        factory = "%{}%".format(factory)
        label = "%{}%".format(label)
        all_data = db.session.query(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).filter((Mocdm_pending.po.like(po)),(Mocdm_pending.style.like(style)),(Mocdm_pending.org_buyer.like(org_buyer)),(Mocdm_pending.color.like(color)),(Mocdm_pending.gp_name.like(gp_name)),(Mocdm_pending.ext_dely.like(ext_dely)),(Mocdm_pending.order_date.like(order_date)),(Mocdm_pending.factory.like(factory)),(Mocdm_pending.label.like(label))).all()
        wb = Workbook()
        ws = wb.active
        ws.append(['PO','LABEL','DES','D/C','PREVIOUS','DELY','MYANMAR','STYLE','BUYER VERSION','BUYER','PRODUCT NAME','MAIN COLOR','SEASON','VESSEL DATE','CATEGORY','MATERIAL CLASSIFICATION','MATERIAL CODE','MATERIAL NAME IN CHINESE','MATERIAL','SIZE','COLOUR','ORIGINAL CONSUME','UNIT','LOSS','CONSUME POINT','ORDER QTY','CONSUME','GROUP','Order Date','FACTORY'])
        for item in all_data:
            ws.append([item.po,item.label,item.des,item.mcn,item.previous,item.ext_dely,item.myanmar,item.style,item.buyer_version,item.pending_buyer,item.product_name,item.main_color,item.season,item.vessel_date,item.category,item.material_classification,item.material_code,item.material,item.material_chinese,item.size,item.color,item.org_consume,item.unit,item.loss,item.consume_point,item.order_qty,item.consume,item.gp,item.order_date,item.factory])
        file = BytesIO()
        wb.save(file)
        file.seek(0)
        filename = 'combination.xlsx'
        r = Response(
            file.read(),
            headers={
                'Content-Disposition': f'attachment;filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
        return r
    else:
        all_data1 = db.session.query(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).all()
        wb = Workbook()
        ws = wb.active
        ws.append(['PO','LABEL','DES','D/C','PREVIOUS','DELY','MYANMAR','STYLE','BUYER VERSION','BUYER','PRODUCT NAME','MAIN COLOR','SEASON','VESSEL DATE','CATEGORY','MATERIAL CLASSIFICATION','MATERIAL CODE','MATERIAL NAME IN CHINESE','MATERIAL','SIZE','COLOUR','ORIGINAL CONSUME','UNIT','LOSS','CONSUME POINT','ORDER QTY','CONSUME','GROUP','Order Date','FACTORY'])
        for item in all_data1:
            ws.append([item.po,item.label,item.des,item.mcn,item.previous,item.ext_dely,item.myanmar,item.style,item.buyer_version,item.pending_buyer,item.product_name,item.main_color,item.season,item.vessel_date,item.category,item.material_classification,item.material_code,item.material,item.material_chinese,item.size,item.color,item.org_consume,item.unit,item.loss,item.consume_point,item.order_qty,item.consume,item.gp,item.order_date,item.factory])
        file = BytesIO()
        wb.save(file)
        file.seek(0)
        filename = 'combination.xlsx'
        r = Response(
            file.read(),
            headers={
                'Content-Disposition': f'attachment;filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
        return r

@auth.route('/download/orderlist', methods=['GET', 'POST'])
def download_report():
    try:
        all_data = db.session.query(Mocdm_erp.po,Mocdm_pending.label,Mocdm_pending.des,Mocdm_pending.mcn,Mocdm_pending.previous,Mocdm_pending.ext_dely,Mocdm_pending.myanmar,Mocdm_erp.style,Mocdm_erp.buyer_version,Mocdm_erp.pending_buyer,Mocdm_erp.product_name,Mocdm_erp.main_color,Mocdm_erp.season,Mocdm_erp.vessel_date,Mocdm_erp.category,Mocdm_erp.material_classification,Mocdm_erp.material_code,Mocdm_erp.material,Mocdm_erp.material_chinese,Mocdm_erp.size,Mocdm_erp.color,Mocdm_erp.org_consume,Mocdm_erp.unit,Mocdm_erp.loss,Mocdm_erp.consume_point,Mocdm_erp.order_qty,Mocdm_erp.consume,Mocdm_erp.gp,Mocdm_pending.order_date,Mocdm_pending.factory).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).all()
        wb = Workbook()
        ws = wb.active
        ws.append(['PO#','LABEL','DES','D/C','PREVIOUS','DELY','MYANMAR','STYLE','BUYER VERSION','BUYER','PRODUCT NAME','MAIN COLOR','SEASON','VESSEL DATE','CATEGORY','MATERIAL CLASSIFICATION','MATERIAL CODE','MATERIAL NAME IN CHINESE','MATERIAL','SIZE','COLOUR','ORIGINAL CONSUME','UNIT','LOSS','CONSUME POINT','ORDER QTY','CONSUME','GROUP','ORDER DATE','FACTORY'])
        for item in all_data:
            ws.append([item.po,item.label,item.des,item.mcn,item.previous.strftime('%d/%m/%Y'),item.ext_dely.strftime('%d/%m/%Y'),item.myanmar,item.style,item.buyer_version,item.pending_buyer,item.product_name,item.main_color,item.season,item.vessel_date.strftime('%d/%m/%Y'),item.category,item.material,item.material_classification,item.material_code,item.material,item.material_chinese,item.size,item.color,item.org_consume,item.unit,item.loss,item.consume_point,item.order_qty,item.consume,item.gp,item.order_date,item.factory])
        file = BytesIO()
        wb.save(file)
        file.seek(0)
        filename = 'combination.xlsx'
        response = Response(
            file.read(),
            headers={
                'Content-Disposition': f'attachment;filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
        return response
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.orderlist'))

@auth.route('/consumptionreport' , defaults={'page_num':1})
@auth.route('/consumptionreport/<int:page_num>', methods=['GET','POST'])
@login_required
def consumptionreport(page_num):
    if request.method=='GET':
        style = request.args.get('style')
        group_name = request.args.get('group_name')
        qty_no = request.args.get('qty_no')
        dely_date = request.args.get('dely_date')
        buyer = request.args.get('buyer')
        all_data = db.session.query(Mocdm_erp.id.label("erpid"),Mocdm_consumption.id,Mocdm_erp.category,Mocdm_erp.material,Mocdm_erp.color,Mocdm_erp.unit,Mocdm_erp.consume,Mocdm_erp.order_qty,Mocdm_consumption.issued_qty,Mocdm_consumption.balance,Mocdm_consumption.date,Mocdm_consumption.issued_by_leader,Mocdm_consumption.factory_line,Mocdm_consumption.reciever,Mocdm_consumption.remark).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).join(Mocdm_consumption,(Mocdm_consumption.erp_id == Mocdm_erp.id),isouter = True).filter(Mocdm_pending.gp_name == group_name,Mocdm_pending.style == style,Mocdm_pending.qty == qty_no,Mocdm_pending.ext_dely == dely_date).paginate(per_page=100, page=page_num, error_out=True)
        return render_template('consumptionreport.html',all_data = all_data, style=style, group_name=group_name, qty_no=qty_no, dely_date=dely_date, buyer=buyer)


@auth.route('/searchcreport', methods=['GET','POST'])
@login_required
def searchcreport():
    try:
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
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.profile'))
       

@auth.route('/consumptionreportUpdate', methods=['GET', 'POST'])
@login_required
def consumptionreportUpdate():
    if request.method=='POST':
        data = Mocdm_consumption.query.get(request.form.get('id'))
        if data:
            style = request.args.get('style')
            group_name = request.args.get('group_name')
            qty_no = request.args.get('qty_no')
            dely_date = request.args.get('dely_date')
            buyer = request.args.get('buyer')
            all_data = Mocdm_consumption(id=request.form['id'],issued_qty=request.form['issued_qty'] or 0,balance=request.form['balance'] or 0,date=request.form['date'] or None,issued_by_leader=request.form['issued_by_leader'] or None,factory_line=request.form['factory_line'] or None,reciever=request.form['reciever'] or None,remark=request.form['remark'] or None)
            db.session.merge(all_data)
            db.session.commit()
            return redirect(request.referrer or url_for('auth.consumptionreport') + '?style=style&group_name=group_name&qty_no=qty_no&dely_date=dely_date&buyer=buyer')
        else:
            style = request.args.get('style')
            group_name = request.args.get('group_name')
            qty_no = request.args.get('qty_no')
            dely_date = request.args.get('dely_date')
            buyer = request.args.get('buyer')
            all_data = Mocdm_consumption(erp_id=request.form['erpid'] ,issued_qty=request.form['issued_qty'] or 0,balance=request.form['balance'] or 0,date=request.form['date'] or None,issued_by_leader=request.form['issued_by_leader'] or None,factory_line=request.form['factory_line'] or None,reciever=request.form['reciever'] or None,remark=request.form['remark'] or None)
            db.session.add(all_data)
            db.session.commit()
            return redirect(request.referrer or url_for('auth.consumptionreport') + '?style=style&group_name=group_name&qty_no=qty_no&dely_date=dely_date&buyer=buyer')

@auth.route('/download/consumptionreport', methods=['GET', 'POST'])
def download_consumptionreportreport():
    try:
        style = request.args.get('style')
        group_name = request.args.get('group_name')
        qty_no = request.args.get('qty_no')
        dely_date = request.args.get('dely_date')
        buyer = request.args.get('buyer')
        all_data = db.session.query(Mocdm_erp.category,Mocdm_erp.material,Mocdm_erp.color,Mocdm_erp.unit,Mocdm_erp.consume,Mocdm_erp.order_qty,Mocdm_consumption.issued_qty,Mocdm_consumption.balance,Mocdm_consumption.date,Mocdm_consumption.issued_by_leader,Mocdm_consumption.factory_line,Mocdm_consumption.reciever,Mocdm_consumption.remark).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).join(Mocdm_consumption,(Mocdm_consumption.erp_id == Mocdm_erp.id),isouter = True).filter(Mocdm_pending.gp_name == group_name,Mocdm_pending.style == style,Mocdm_pending.qty == qty_no,Mocdm_pending.ext_dely == dely_date).all()       
        wb = Workbook()
        ws = wb.active
        ws.merge_cells('J1:M1')
        
        ws['J1'] = 'Manager'
        ws['J2'] = ''
        ws['J1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.append(['Style','Group Name','Qty','Dely Date','Buyer'])
        ws.append([style,group_name,qty_no,dely_date,buyer])
        ws.append(['CATEGORY','MATERIAL','COLOUR','UNIT','CONSUME','ORDER QTY','ISSUED QTY','BALANCE','DATE','ISSUED BY (Leader)','Factory line','RECEIVER','REMARK','SIGN'])
        for item in all_data:
            ws.append([item.category,item.material,item.color,item.unit,item.consume,item.order_qty,item.issued_qty,item.balance,item.date,item.issued_by_leader,item.factory_line,item.reciever,item.remark])
        file = BytesIO()
        wb.save(file)
        file.seek(0)
        filename = 'consumptionsreport.xlsx'
        r = Response(
            file.read(),
            headers={
                'Content-Disposition': f'attachment;filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
        return r
        
        # output = io.BytesIO()
        # # workbook = openpyxl.Workbook()
        # wb = Workbook()
        # worksheet = wb.active
        # worksheet.title = 'Example'
        # worksheet.cell(row=1, column=1, value=((['CATEGORY','MATERIAL','COLOUR','UNIT','CONSUME','ORDER QTY','ISSUED QTY','BALANCE','DATE','ISSUED BY (Leader)','Factory line','RECEIVER','REMARK'])))
        # worksheet.cell(row=1, column=2, value=(['CATEGORY','MATERIAL','COLOUR','UNIT','CONSUME','ORDER QTY','ISSUED QTY','BALANCE','DATE','ISSUED BY (Leader)','Factory line','RECEIVER','REMARK']))
        # for i, example in enumerate(all_data, start=2):
        #     worksheet.cell(row=i, column=1, value=[example.category,example.material,example.color,example.unit,example.consume,example.order_qty,example.issued_qty,example.balance,example.date,example.issued_by_leader,example.factory_line,example.reciever,example.remark])
        #     # worksheet.cell(row=i, column=2, value=example.column2)
        # workbook.save(output)
        # output.seek(0)
        # response = make_response(output.getvalue())
        # response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        # response.headers['Content-Disposition'] = 'attachment; filename=example.xlsx'
        # return response


        # df = pd.DataFrame((tuple(t) for t in all_data), columns=('CATEGORY','MATERIAL','COLOUR','UNIT','CONSUME','ORDER QTY','ISSUED QTY','BALANCE','DATE','ISSUED BY (Leader)','Factory line','RECEIVER','REMARK'))
        # out = io.BytesIO()
        # writer = pd.ExcelWriter(out, engine='openpyxl')
        # df.to_excel(excel_writer=writer, index=False, sheet_name='Sheet1')
        # writer.save()
        # writer.close()
        # r = make_response(out.getvalue())
        # r.headers["Content-Disposition"] = "attachment; filename=consumptionreport.xlsx"
        # r.headers["Content-type"] = "application/x-xls"

        # return r 
    except SQLAlchemyError as e:
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logging.basicConfig(filename= f'error_log.log', level=logging.ERROR)
        logging.error(str(e))
    return redirect(url_for('auth.profile'))

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
        return render_template('schedulereport.html',all_data = all_data, schedule_active="is_active('/schedule')")

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

# @auth.route('/consump_list', defaults={'page_num':1})
# @auth.route('/consump_list/<int:page_num>', methods=['GET', 'POST'])
# @login_required
# def consump_list(page_num):
@auth.route('/consump_list')
def consump_list():
    all_data = db.session.query(Mocdm_pending.factory, Mocdm_pending.gp_name, Mocdm_pending.qty, 
                      Mocdm_pending.ext_dely, Mocdm_pending.style, Mocdm_pending.org_buyer)\
              .group_by(Mocdm_pending.factory, Mocdm_pending.gp_name, Mocdm_pending.qty, 
                        Mocdm_pending.ext_dely, Mocdm_pending.style, Mocdm_pending.org_buyer).all()
    return render_template('consumpList.html', all_data=all_data, consump_active="is_active('/consump')")
    # else:
        # po = request.form['po']
        # style = request.form['style']
        # org_buyer = request.form['org_buyer']
        # color = request.form['color']
        # order_date = request.form['order_date']
        # des = request.form['des']
        # gp_name = request.form['gp_name']
        # ext_dely = request.form['ext_dely']
        # factory = request.form['factory']
        # session['po'] = po
        # session['style'] = style
        # session['org_buyer'] = org_buyer
        # session['color'] = color
        # session['gp_name'] = gp_name
        # session['ext_dely'] = ext_dely
        # session['order_date'] = order_date
        # session['factory'] = factory
        # session['des'] = des
        # search1 = "%{}%".format(po)
        # search2 = "%{}%".format(style)
        # search3 = "%{}%".format(org_buyer)
        # search4 = "%{}%".format(color)
        # search5 = "%{}%".format(order_date)
        # search6 = "%{}%".format(des)
        # search7 = "%{}%".format(gp_name)
        # search8 = "%{}%".format(ext_dely)
        # search9 = "%{}%".format(factory)
        # all_data = Mocdm_pending.query.filter((Mocdm_pending.po.like(search1)),(Mocdm_pending.style.like(search2)),(Mocdm_pending.org_buyer.like(search3)),(Mocdm_pending.color.like(search4)),(Mocdm_pending.order_date.like(search5)),(Mocdm_pending.des.like(search6)),(Mocdm_pending.gp_name.like(search7)),(Mocdm_pending.ext_dely.like(search8)),(Mocdm_pending.factory.like(search9))).group_by(Mocdm_pending.factory, Mocdm_pending.gp_name, Mocdm_pending.qty,Mocdm_pending.ext_dely, Mocdm_pending.style, Mocdm_pending.org_buyer).paginate(per_page=100, page=page_num, error_out=True)
        # return render_template("consumpList.html", po=po,style=style,org_buyer=org_buyer,color=color,order_date=order_date,des=des,gp_name=gp_name,ext_dely=ext_dely,factory=factory,all_data=all_data, consump_active="is_active('/consump')")

# @auth.route('/consump_search', methods=['GET', 'POST'])
# def consump_search():
#     if request.method=='POST':
#         po = request.form['po']
#         style = request.form['style']
#         org_buyer = request.form['org_buyer']
#         color = request.form['color']
#         order_date = request.form['order_date']
#         des = request.form['des']
#         gp_name = request.form['gp_name']
#         ext_dely = request.form['ext_dely']
#         factory = request.form['factory']
#         session['po'] = po
#         session['style'] = style
#         session['org_buyer'] = org_buyer
#         session['color'] = color
#         session['gp_name'] = gp_name
#         session['ext_dely'] = ext_dely
#         session['order_date'] = order_date
#         session['factory'] = factory
#         session['des'] = des
#         search1 = "%{}%".format(po)
#         search2 = "%{}%".format(style)
#         search3 = "%{}%".format(org_buyer)
#         search4 = "%{}%".format(color)
#         search5 = "%{}%".format(order_date)
#         search6 = "%{}%".format(des)
#         search7 = "%{}%".format(gp_name)
#         search8 = "%{}%".format(ext_dely)
#         search9 = "%{}%".format(factory)
#         all_data = Mocdm_pending.query.filter((Mocdm_pending.po.like(search1)),(Mocdm_pending.style.like(search2)),(Mocdm_pending.org_buyer.like(search3)),(Mocdm_pending.color.like(search4)),(Mocdm_pending.order_date.like(search5)),(Mocdm_pending.des.like(search6)),(Mocdm_pending.gp_name.like(search7)),(Mocdm_pending.ext_dely.like(search8)),(Mocdm_pending.factory.like(search9))).group_by(Mocdm_pending.factory, Mocdm_pending.gp_name, Mocdm_pending.qty, 
#                         Mocdm_pending.ext_dely, Mocdm_pending.style, Mocdm_pending.org_buyer).all()
#         return render_template("consumpList.html", all_data = all_data, consump_active="is_active('/consump')")

@auth.route('/consumption_list_report' , defaults={'page_num':1})
@auth.route('/consumption_list_report/<int:page_num>', methods=['GET','POST'])
@login_required
def consumption_list_report(page_num):
    # try:
        if request.method=='GET':
            factory = request.args.get('factory')
            gp_name = request.args.get('gp_name')
            qty = request.args.get('qty')
            ext_dely = request.args.get('ext_dely')
            date_object = datetime.strptime(ext_dely, "%Y-%m-%d").date()
            new_date_string = date_object.strftime("%m/%d/%Y")
            style = request.args.get('style')
            org_buyer = request.args.get('org_buyer')
            all_data = db.session.query(Mocdm_erp.id.label("erpid"),Mocdm_consumption.id,Mocdm_erp.category,Mocdm_erp.material,Mocdm_erp.color,Mocdm_erp.unit,Mocdm_erp.consume,Mocdm_erp.order_qty,Mocdm_consumption.issued_qty,Mocdm_consumption.balance,Mocdm_consumption.date,Mocdm_consumption.issued_by_leader,Mocdm_consumption.factory_line,Mocdm_consumption.reciever,Mocdm_consumption.remark,Mocdm_pending.qty).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).join(Mocdm_consumption,(Mocdm_consumption.erp_id == Mocdm_erp.id),isouter = True).filter(Mocdm_pending.factory == factory,Mocdm_pending.gp_name == gp_name,Mocdm_pending.qty == qty,Mocdm_pending.ext_dely == ext_dely,Mocdm_pending.style == style,Mocdm_pending.org_buyer == org_buyer).paginate(per_page=100, page=page_num, error_out=True)
            print(all_data)
            return render_template('consumptionlistreport.html',factory=factory, gp_name=gp_name, qty=qty, ext_dely=new_date_string, style=style, org_buyer=org_buyer, all_data = all_data)
    # except SQLAlchemyError as e:
    #     current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #     logging.basicConfig(filename= f'error_log.log', level=logging.DEBUG)
    #     logging.error(str(e))
    # return render_template('consumptionlistreport.html',factory=factory, gp_name=gp_name, qty=qty, ext_dely=new_date_string, style=style, org_buyer=org_buyer, all_data = all_data)

@auth.route('/download/consumption_list_report', methods=['GET', 'POST'])
def download_consumptionlistreportreport():
        factory = request.args.get('factory')
        gp_name = request.args.get('gp_name')
        qty = request.args.get('qty')
        ext_dely = request.args.get('ext_dely')
        date_object = datetime.strptime(ext_dely, "%m/%d/%Y").date()
        new_date_string = date_object.strftime("%Y-%m-%d")
        style = request.args.get('style')
        org_buyer = request.args.get('org_buyer')
        all_data = db.session.query(Mocdm_erp.id.label("erpid"),Mocdm_consumption.id,Mocdm_erp.category,Mocdm_erp.material,Mocdm_erp.color,Mocdm_erp.unit,Mocdm_erp.consume,Mocdm_erp.order_qty,Mocdm_pending.qty,Mocdm_consumption.issued_qty,Mocdm_consumption.balance,Mocdm_consumption.date,Mocdm_consumption.issued_by_leader,Mocdm_consumption.factory_line,Mocdm_consumption.reciever,Mocdm_consumption.remark).join(Mocdm_pending,(Mocdm_pending.po == Mocdm_erp.po) & (Mocdm_pending.color == Mocdm_erp.main_color) & (Mocdm_pending.style == Mocdm_erp.style) & (Mocdm_pending.org_buyer == Mocdm_erp.pending_buyer),isouter = True).join(Mocdm_consumption,(Mocdm_consumption.erp_id == Mocdm_erp.id),isouter = True).filter(Mocdm_pending.factory == factory,Mocdm_pending.gp_name == gp_name,Mocdm_pending.qty == qty,Mocdm_pending.ext_dely == new_date_string,Mocdm_pending.style == style,Mocdm_pending.org_buyer == org_buyer).all()       
        wb = Workbook()
        ws = wb.active
        ws.merge_cells('J1:M1')
        ws['J1'] = 'Manager'
        ws['J2'] = ''
        ws['J1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.append(['Factory','Group','Qty','Dely','STYLE','BUYER'])
        ws.append([factory,gp_name,qty,ext_dely,org_buyer])
        ws.append(['CATEGORY','MATERIAL','COLOUR','CONSUME','QTY','TOTAL QTY','ISSUED QTY','BALANCE','DATE','ISSUED BY (Leader)','Factory line','RECEIVER','REMARK','SIGN'])
        for item in all_data:
            ws.append([item.category,item.material,item.color,item.qty,item.consume,item.order_qty,item.issued_qty,item.balance,item.date,item.issued_by_leader,item.factory_line,item.reciever,item.remark])
        file = BytesIO()
        wb.save(file)
        file.seek(0)
        filename = 'consumptionsreport.xlsx'
        r = Response(
            file.read(),
            headers={
                'Content-Disposition': f'attachment;filename={filename}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
        return r


@auth.route('/deltamate', methods=['GET', 'POST'])
def deltamate():
    data_date = []
    data_arr = {}
    final_arr = {}
    response = {}

    s_date = datetime.strptime('2023-03-13', '%Y-%m-%d')
    e_date = datetime.strptime('2023-03-28', '%Y-%m-%d')

    while s_date <= e_date:
        data_date.append(s_date.strftime('%Y-%m-%d'))
        s_date += timedelta(days=1)

    for date in data_date:
        final_arr[date] = {}

    result = [
        {'line':1, 'del_date':'2023-05-05', 'qty':700, 'target':1000, 'balance':1000, 'zip_thread':1000, 'group':'MORA', 'style':'LJ-0423C', 'version':'2', 'buyer':'AF3114E0305', 'data_date':'2023-03-13'},
        {'line':1, 'del_date':'2023-05-05', 'qty':700, 'target':1000, 'balance':1000, 'zip_thread':1000, 'group':'MORA', 'style':'LJ-0423C', 'version':'2', 'buyer':'AF3114E0305', 'data_date':'2023-03-14'},
        {'line':1, 'del_date':'2023-05-05', 'qty':700, 'target':1000, 'balance':1000, 'zip_thread':1000, 'group':'MORA', 'style':'LJ-0423C', 'version':'2', 'buyer':'AF3114E0305', 'data_date':'2023-03-15'},
        {'line':2, 'del_date':'2023-05-05', 'qty':700, 'target':1000, 'balance':1000, 'zip_thread':1000, 'group':'MORA', 'style':'LJ-0423C', 'version':'2', 'buyer':'AF3114E0305', 'data_date':'2023-03-13'},
        {'line':3, 'del_date':'2023-05-05', 'qty':700, 'target':1000, 'balance':1000, 'zip_thread':1000, 'group':'MORA', 'style':'LJ-0423C', 'version':'2', 'buyer':'AF3114E0305', 'data_date':'2023-03-13'},
        {'line':3, 'del_date':'2023-05-05', 'qty':700, 'target':1000, 'balance':1000, 'zip_thread':1000, 'group':'MORA', 'style':'LJ-0423C', 'version':'2', 'buyer':'AF3114E0305', 'data_date':'2023-03-15'}
    ]

    for row in result:
        data_arr.setdefault(row['line'], []).append(row)

    for key, row in data_arr.items():
        for x in data_date:
            final_arr[x] = {}

        for row in row:
            final_arr[row['data_date']] = row

        response[key] = final_arr

    return render_template('dd.html', data_date=data_date)