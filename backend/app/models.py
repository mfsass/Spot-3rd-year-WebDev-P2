from flask import request, jsonify
from datetime import datetime
from functools import wraps
import jwt

from app import db, ma, app

from sqlalchemy.ext.associationproxy import association_proxy

###################
#    Tables
################### 

class Friendship(db.Model):
    friend_request_from_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True) # the one that requests
    friend_request_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True) # the one that accepts the request
    accepted = db.Column(db.Boolean, default=False)

    # friend_request_from
    # friend_request_to

    def __init__(self, friend_request_from_id, friend_request_to_id):
        self.friend_request_from_id = friend_request_from_id
        self.friend_request_to_id = friend_request_to_id


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32))
    email = db.Column(db.String(32))
    password_hash = db.Column(db.String(128))
    avatar_url = db.Column(db.String(2048))

    posts = db.relationship('Post', backref='user', cascade='all, delete')
    comments = db.relationship('Comment', backref='user', cascade='all, delete')
    
    memberships = db.relationship('Membership', backref='user', cascade='all, delete')
    groups = association_proxy("memberships", "group")

    friendships_request_to = db.relationship('Friendship', backref='friend_request_from', primaryjoin=id==Friendship.friend_request_from_id, cascade='all, delete')
    friendships_request_from = db.relationship('Friendship', backref='friend_request_to', primaryjoin=id==Friendship.friend_request_to_id, cascade='all, delete')
    
    # friends_request_to = association_proxy('friendships_request_to', 'friend_request_to')
    # friends_request_from = association_proxy('friendships_request_from', 'friend_request_from')

    def __init__(self, username, email, avatar_url, password_hash):
        self.username = username
        self.email = email
        self.avatar_url = avatar_url
        self.password_hash = password_hash


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))

    posts = db.relationship('Post', backref='group', cascade='all, delete')
    memberships = db.relationship('Membership', backref='group', cascade='all, delete')
    users = association_proxy("memberships", "user")

    def __init__(self, name):
        self.name = name
 

class Membership(db.Model):
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    admin = db.Column(db.Boolean)

#   group
#   user  

    def __init__(self, group_id, user_id, admin):
        self.group_id = group_id
        self.user_id = user_id
        self.admin = admin


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    video_url = db.Column(db.String(2048))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    longitude = db.Column(db.DECIMAL(13,10))
    latitude = db.Column(db.DECIMAL(13,10))
    category = db.Column(db.String(32)) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))

    comments = db.relationship('Comment', backref='post', cascade='all, delete')
#   user
#   group

    def __init__(self, text, video_url, longitude, latitude, category):
        self.text = text
        self.video_url = video_url
        self.longitude = longitude
        self.latitude = latitude
        self.category = category    


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

#   post
#   user 

    def __init__(self, text):
        self.text = text


###################
#   Schemas
###################

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'email', 'avatar_url')
user_schema = UserSchema()
users_schema = UserSchema(many=True)

class GroupSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name')
group_schema = GroupSchema()
groups_schema = GroupSchema(many=True)

class MembershipSchema(ma.Schema):
    class Meta:
        fields = ('id', 'group.name', 'user.username', 'admin')
membership_schema = GroupSchema()
memberships_schema = GroupSchema(many=True)

class PostSchema(ma.Schema):
    class Meta:
        fields = ('id', 'text','video_url', 'date', 'longitude', 'latitude', 'category', 'user.username', 'group.name')
post_schema = PostSchema()
posts_schema = PostSchema(many=True)

class CommentSchema(ma.Schema):
    class Meta:
        fields = ('id', 'text', 'date', 'user.username')
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)


###################
#  Authentication
###################

def token_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):
       token = None
       if 'access-token' in request.headers:
           token = request.headers['access-token']
 
       if not token:
           return jsonify({'message': 'a valid token is missing'})
       try:
           data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
           current_user = User.query.filter_by(id=data['id']).first()
       except:
           return jsonify({
               'timeout':True,
               'message': 'token is invalid'})
 
       return f(current_user, *args, **kwargs)
   return decorator


db.create_all()
db.session.commit()