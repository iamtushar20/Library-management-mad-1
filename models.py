from app import app

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime





app.app_context().push()

db = SQLAlchemy(app)



# Defining SQLAlchemy models for  database schema
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column (db.String(255), nullable=False)
    date_created = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    authors = db.Column(db.String(255), nullable=False)
    date_added = db.Column(db.Date)
    price = db.Column(db.Integer, nullable=False)
    
    section = db.relationship('Section', backref='books')



class BookRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(255), db.ForeignKey('user.username'),nullable=False)
    book_name = db.Column(db.String(255), db.ForeignKey('book.name'), nullable=False)
    request_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    status = db.Column(db.String(255), default='pending', nullable=False)
    user = db.relationship('User', backref='book_requests')
    book = db.relationship('Book', backref='book_requests')

class BookIssue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(255), db.ForeignKey('user.username'), nullable=False)
    book_name = db.Column(db.String(255), db.ForeignKey('book.name'), nullable=False)
    book_author = db.Column(db.String(255), db.ForeignKey('book.authors'), nullable=False)
    issue_date = db.Column(db.Date, db.ForeignKey('book_request.request_date'), nullable=False)
    return_date = db.Column(db.Date, db.ForeignKey('book_request.return_date'))
    approved = db.Column(db.String(255),db.ForeignKey('book_request.status'), nullable=False)
    read = db.Column(db.String(255), db.ForeignKey('book.content'))
    feedback = db.Column(db.String(255), nullable=True)


    
    
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        password_hash = 1111
        admin = User(username='admin', password=password_hash, name='Admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()


