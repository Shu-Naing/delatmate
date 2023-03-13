from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from __init__ import db

class Mocdm_users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    name = db.Column(db.String(255))
    phone = db.Column(db.String(255))
    role = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Mocdm_erp(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    po = db.Column(db.String(255))
    style = db.Column(db.String(255))
    buyer_version = db.Column(db.String(255))
    buyer = db.Column(db.String(255))
    product_name = db.Column(db.String(255))
    main_color = db.Column(db.String(255))
    season = db.Column(db.String(255))
    vessel_date = db.Column(db.Date)
    category = db.Column(db.String(255))
    material_classification = db.Column(db.String(255))
    material_code = db.Column(db.String(255))
    material = db.Column(db.String(255))
    material_chinese = db.Column(db.String(255))
    size = db.Column(db.String(255))
    color = db.Column(db.String(255))
    org_consume = db.Column(db.String(255))
    unit = db.Column(db.String(255))
    loss = db.Column(db.String(255))
    consume_point = db.Column(db.String(255))
    order_qty = db.Column(db.Integer)
    consume = db.Column(db.String(255))
    gp = db.Column(db.String(255))
    remark = db.Column(db.String(255))
    status = db.Column(db.String(255))
    pending_buyer = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Mocdm_pending(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    ext_dely = db.Column(db.Date)
    mcn = db.Column(db.String(255))
    po = db.Column(db.String(255))
    ship_to = db.Column(db.String(255))
    label = db.Column(db.String(255))
    linked_store = db.Column(db.String(255))
    des = db.Column(db.String(255))
    gp_name = db.Column(db.String(255))
    style = db.Column(db.String(255))
    org_buyer = db.Column(db.String(255))
    color = db.Column(db.String(255))
    qty = db.Column(db.Integer)
    vessel_date = db.Column(db.Date)
    factory = db.Column(db.String(255))
    db_gb_code = db.Column(db.String(255))
    sdn_po = db.Column(db.String(255))
    customer_po = db.Column(db.String(255))
    upc_no = db.Column(db.String(255))
    linked_so_no = db.Column(db.String(255))
    ref_no = db.Column(db.String(255))
    material_log_no = db.Column(db.String(255))
    season = db.Column(db.String(255))
    buyer_txt = db.Column(db.String(255))
    order_date = db.Column(db.Date)
    kmz_id = db.Column(db.Integer)
    remark = db.Column(db.String(255))
    shpg_job = db.Column(db.String(255))
    xfty_date = db.Column(db.String(255))
    status = db.Column(db.String(255))
    previous = db.Column(db.Date)
    myanmar = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Mocdm_consumption(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    erp_id = db.Column(db.Integer)
    issued_qty = db.Column(db.Integer, default=0)
    balance = db.Column(db.Integer, default=0)
    date = db.Column(db.Date)
    issued_by_leader = db.Column(db.String(255))
    factory_line = db.Column(db.String(255))
    reciever = db.Column(db.String(255))
    remark = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Mocdm_schedule(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    line = db.Column(db.String(255))
    dely = db.Column(db.Date)
    qty = db.Column(db.Integer)
    target = db.Column(db.String(255))
    balance = db.Column(db.String(255))
    zip_thread= db.Column(db.String(255))
    group = db.Column(db.String(255))
    style = db.Column(db.String(255))
    version = db.Column(db.String(255))
    image_path = db.Column(db.String(255))
    buyer = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, onupdate=datetime.utcnow)