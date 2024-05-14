from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)

# Define Ticket model
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    assignee = db.Column(db.String(255))
    raised_by = db.Column(db.String(255), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)

    # Relationship with comments
    comments = db.relationship('Comment', backref='ticket', lazy=True, cascade="all, delete-orphan")

    # Relationship with attachments
    attachments = db.relationship('Attachment', backref='ticket', lazy=True, cascade="all, delete-orphan")

# Define Comment model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    username = db.Column(db.String(255))
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id', ondelete='CASCADE'), nullable=False)

# Define Attachment model
class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    username = db.Column(db.String(255))
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id', ondelete='CASCADE'), nullable=False)

