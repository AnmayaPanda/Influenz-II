from flask_sqlalchemy import SQLAlchemy
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    passhash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    influencer_profile = db.relationship('Influencer', back_populates='user', uselist=False)
    sponsor = db.relationship('Sponsor', backref='user', uselist=False)
    @property
    def password(self):
        raise AttributeError('password is not readable attribute')

    @password.setter
    def password(self,password):
        self.passhash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.passhash,password)

class Sponsor(db.Model):
    __tablename__ = 'sponsor'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    company_name = db.Column(db.String(150))
    industry = db.Column(db.String(150))
    budget = db.Column(db.Float)
    campaigns = db.relationship('Campaign', backref='sponsor', lazy=True)

class Influencer(db.Model):
    __tablename__ = 'influencer'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    category = db.Column(db.String(150))
    niche = db.Column(db.String(150))
    reach = db.Column(db.Integer)
    ad_requests = db.relationship('AdRequest', backref='influencer', lazy=True)
    user = db.relationship('User', back_populates='influencer_profile')

class Campaign(db.Model):
    __tablename__ = 'campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(50), nullable=False) # 'public', 'private'
    goals = db.Column(db.Text, nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    ad_requests = db.relationship('AdRequest', backref='campaign', lazy=True)

class AdRequest(db.Model):
    __tablename__ = 'ad_request'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    messages = db.Column(db.Text)
    requirements = db.Column(db.Text, nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False) # 'Pending', 'Accepted', 'Rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FlaggedUser(db.Model):
    __tablename__ = 'flagged_user'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    flagged_at = db.Column(db.DateTime, default=datetime.utcnow)

class FlaggedCampaign(db.Model):
    __tablename__ = 'flagged_campaign'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    flagged_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    ad_request_id = db.Column(db.Integer, db.ForeignKey('ad_request.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()