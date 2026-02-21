from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    jobs = db.relationship('Job', backref='user', lazy=True)
    chats = db.relationship('Chat', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_path = db.Column(db.String(500), nullable=False)
    ocr_status = db.Column(db.String(20), default='pending')
    whisper_status = db.Column(db.String(20), default='pending')
    llm_status = db.Column(db.String(20), default='pending')
    final_status = db.Column(db.String(20), default='pending')
    status_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lecture = db.relationship('Lecture', backref='job', uselist=False, lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'video_path': self.video_path,
            'ocr_status': self.ocr_status,
            'whisper_status': self.whisper_status,
            'llm_status': self.llm_status,
            'final_status': self.final_status,
            'status_message': self.status_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_complete(self):
        return self.final_status == 'done'
    
    def has_failed(self):
        return self.final_status == 'failed'
    
    def is_cancelled(self):
        return self.final_status == 'cancelled'
    
    def is_processing(self):
        return (self.ocr_status in ['running', 'pending'] or 
                self.whisper_status in ['running', 'pending'] or
                self.llm_status in ['running', 'pending'])
    
    def can_cancel(self):
        if self.final_status in ('done', 'failed', 'cancelled'):
            return False
        return True

class Lecture(db.Model):
    __tablename__ = 'lectures'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), unique=True, nullable=False)
    summary = db.Column(db.Text)
    notes_path = db.Column(db.String(500))
    transcript_path = db.Column(db.String(500))
    
    chats = db.relationship('Chat', backref='lecture', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'summary': self.summary,
            'notes_path': self.notes_path,
            'transcript_path': self.transcript_path
        }

class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'lecture_id': self.lecture_id,
            'user_id': self.user_id,
            'question': self.question,
            'answer': self.answer,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
