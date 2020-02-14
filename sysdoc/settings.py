from flask import Flask, session, redirect
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy # sql operations
from sqlalchemy.sql import func
from sqlalchemy import Table, Text, Column, ForeignKey
from flask_sslify import SSLify
from flask_static_compress import FlaskStaticCompress
from flask_compress import Compress
from flask_cors import CORS
import pytz
import flask_excel as excel
from sqlalchemy.sql.functions import ReturnTypeFromArgs
WEBPUSH_VAPID_PRIVATE_KEY = 'SpfSYqFUN8BrfLTujqsd3zDctEn7KVCKujRPlWhfDPs'
NOT_ALLOWED_EXTENSIONS=["docx","pdf"]
#Override Flask class to secure private data
class SecuredStaticFlask(Flask):
	def send_static_file(self, filename):
		if filename.rsplit('.', 1)[1].lower() not in NOT_ALLOWED_EXTENSIONS:
			return super(SecuredStaticFlask, self).send_static_file(filename)
		else:
			if 'username' in session:
				username = session['username']
				logged=User.query.filter_by(cpf=session['username_cpf']).first()
				if logged.category<=2:
					return super(SecuredStaticFlask, self).send_static_file(filename)
				else:
					redirect('/')
		return redirect('/')

application = SecuredStaticFlask(__name__, static_url_path='/static')
sslify = SSLify(application, subdomains=True, permanent=True)
login = LoginManager(application)
login.login_view = 'admin.login'
application.debug=False;
application.secret_key = "9bc3819243c6949d1ae119b8d2cac52c"
application.config['SQLALCHEMY_DATABASE_URI']='postgres://docs:123405@localhost/docs'
application.config['SQLALCHEMY_BINDS'] = {
    'alumni': 'postgres://docs:123405@localhost/alumni'
}
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config['SERVER_NAME'] = 'fundacaocefetminas.org.br'
db=SQLAlchemy(application)
excel.init_excel(application)
compress = FlaskStaticCompress(application)
Compress(application)
CORS(application)
TEMPLATE_UPLOAD_FOLDER="static/templates"
SIGNATURE_UPLOAD_FOLDER="static/signatures"
SIGNATURE_EXAMPLES_FOLDER="static/signatures/examples"
POST_IMAGES_UPLOAD_FOLDER="static/post_images"
PROFILEPIC_UPLOAD_FOLDER="static/profilepic"
ATTACHMENT_UPLOAD_FOLDER="static/attachments"
BACKUP_FOLDER="static/backup"
TIMEZONE= pytz.timezone('Brazil/East')
GMT_TIMEZONE = pytz.timezone('UTC')

user_events = Table('user_events', db.metadata,
    Column('user_id', ForeignKey('user.id'), primary_key=True),
    Column('event_id', ForeignKey('event.id'), primary_key=True)
)

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	cpf = db.Column(db.String(255))
	email = db.Column(db.String(255))
	password = db.Column(db.String(255))
	profilepicturepath = db.Column(db.String(255))
	security_code = db.Column(db.String(255))
	category = db.Column(db.Integer)
	passwordchangerequest = db.Column(db.Boolean)
	blocked = db.Column(db.Boolean)
	last_login = db.Column(db.DateTime)
	locked = db.Column(db.Boolean)
	token = db.Column(db.String(255))
	last_token = db.Column(db.DateTime)
	documents = db.relationship('Document', backref='user', lazy='dynamic')
	logs = db.relationship('Log', backref='user', lazy='dynamic')
	signature = db.relationship('Signature', backref='user', lazy='dynamic')
	notifications = db.relationship('Notification', backref='user', lazy='dynamic')
	events_own = db.relationship('Event_Administrator', back_populates='user')
	events = db.relationship('Event',secondary=user_events, back_populates='users')
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	comments = db.relationship('Post_Comment', backref='author', lazy='dynamic')
	contexts = db.relationship('User_Context',	back_populates='user')
	subscriptions = db.relationship('User_Subscription',	back_populates='user')
	def __init__(self, name, cpf, email, password,category,passwordchangerequest,blocked):
		self.name = name
		self.cpf = cpf
		self.email = email
		self.password = password
		self.category = category
		self.passwordchangerequest = passwordchangerequest
		self.blocked = blocked
	def __repr__(self):
		return '<User name: %r>' % self.name
	def __lt__(self, other):
         return self.name < other.name
	def getprofilepic(self):
		if self.profilepicturepath is None or self.profilepicturepath =="":
			return '/static/profilepic/default.png';
		else:
			return '/'+self.profilepicturepath;


class Template(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	description = db.Column(db.Text)
	event_id =  db.Column(db.Integer, db.ForeignKey('event.id'))
	path = db.Column(db.String(255))
	file_name = db.Column(db.String(255))
	documents = db.relationship('Document', backref='template', lazy='dynamic')
	fields = db.relationship('Field', backref='template', lazy='dynamic')
	attachments = db.relationship('Attachment', backref='template', lazy='dynamic')
	signatures = db.relationship(
		'Templates_Signatures',
		back_populates='template'
    )
	def __init__(self, name, description,path,event,file_name):
		self.name = name
		self.description = description
		self.path=path
		self.event=event
		self.file_name=file_name

	def __repr__(self):
		return '<Template name:%r>' % self.name

class Event(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(255))
	coordinator = db.Column(db.String(255))
	abstract = db.Column(db.Text)
	startDate = db.Column(db.Text)
	endDate = db.Column(db.Text)
	workload = db.Column(db.Text)
	place = db.Column(db.Text)
	participantsNumber = db.Column(db.Integer)
	administrators =  db.relationship('Event_Administrator', back_populates='event')
	templates = db.relationship('Template', backref='event', lazy='dynamic')
	users = db.relationship('User', secondary=user_events, back_populates='events')
	def __init__(self, title, coordinator, abstract, startDate, endDate, workload, place, participantsNumber):
		self.title = title
		self.coordinator = coordinator
		self.abstract = abstract
		self.startDate = startDate
		self.endDate = endDate
		self.workload = workload
		self.place = place
		self.participantsNumber = participantsNumber

	def __repr__(self):
		return '<Event title:%r>' % self.title


class Event_Administrator(db.Model):
	__tablename__ = 'event_administrator'
	user_id = db.Column(db.Integer, ForeignKey('user.id'), primary_key=True)
	event_id = db.Column(db.Integer, ForeignKey('event.id'), primary_key=True)
	user = db.relationship("User", back_populates="events_own")
	event = db.relationship("Event", back_populates="administrators")
	def __init__(self, user, event):
		self.user=user
		self.event=event
	def __repr__(self):
		return '<Event_Administrator user_id:%r>' % self.user_id



class Field(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	template_id = db.Column(db.Integer, db.ForeignKey('template.id'))
	name = db.Column(db.String(255))
	values = db.relationship('Value', backref='field', lazy='dynamic')
	def __init__(self,template,name):
		self.template=template
		self.name = name

	def __repr__(self):
		return '<Field name:%r>' % self.name

class Seed(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	value = db.Column(db.Integer)

	def __init__(self, name, value):
		self.name=name
		self.value=value
	def __repr__(self):
		return '<Seed name:%r>' % self.name

class Log(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, server_default=func.now())
	action = db.Column(db.String(255))
	document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	additional = db.Column(db.String(255))
	def __init__(self, user, action, document):
		self.user=user
		self.document=document
		self.action=action
	def __repr__(self):
		return '<Log date:%r>' % self.date

class TimerLog(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, server_default=func.now())
	time = db.Column(db.Interval)
	operation = db.Column(db.Integer)
	generic_id = db.Column(db.Integer)
	additional = db.Column(db.String(255))
	def __init__(self, time, operation, generic_id, additional=None):
		self.time=time
		self.operation=operation
		self.generic_id=generic_id
		self.additional=additional
	def __repr__(self):
		return '<TimerLog generic_id:%r>' % self.generic_id


class Systemsettings(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	key = db.Column(db.String(255))
	value = db.Column(db.String(255))
	def __init__(self, key, value):
		self.key=key
		self.value=value
	def __repr__(self):
		return '<Systemsettings key:%r>' % self.key

class Document(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	available = db.Column(db.Boolean)
	code = db.Column(db.String(255))
	template_id = db.Column(db.Integer, db.ForeignKey('template.id'))
	logs = db.relationship('Log', backref='document', lazy='dynamic')
	user_id =  db.Column(db.Integer, db.ForeignKey('user.id'))
	values = db.relationship('Value', backref='document', lazy='dynamic')
	signatures = db.relationship(
		'Documents_Signatures',
		back_populates='document'
	)
	def __init__(self, template,user,available):
		self.template=template
		self.user=user
		self.available=available

	def __repr__(self):
		return '<Document name:%r>' % self.user.name

class Value(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	field_id = db.Column(db.Integer, db.ForeignKey('field.id'))
	value = db.Column(db.String(255))
	document_id = db.Column(db.Integer, db.ForeignKey('document.id'))

	def __init__(self, value,field,document):
		self.value=value
		self.field=field
		self.document=document

	def __repr__(self):
		return '<Value value:%r>' % self.value

class Signature(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	path = db.Column(db.String(255))
	user_id =  db.Column(db.Integer, db.ForeignKey('user.id'))
	templates = db.relationship(
        'Templates_Signatures',
		back_populates='signature'
    )
	documents = db.relationship(
        'Documents_Signatures',
		back_populates='signature'
    )
	def __init__(self, user, path):
		self.user=user
		self.path=path

	def __repr__(self):
		return '<Signature path:%r>' % self.path

class Documents_Signatures(db.Model):
	__tablename__ = 'documents_signatures'
	document_id = db.Column(db.Integer, ForeignKey('document.id'), primary_key=True)
	signature_id = db.Column(db.Integer, ForeignKey('signature.id'), primary_key=True)
	authorized = db.Column(db.Integer)
	request_date = db.Column(db.DateTime)
	authorization_date = db.Column(db.DateTime)
	document = db.relationship("Document", back_populates="signatures")
	signature = db.relationship("Signature", back_populates="documents")
	def __repr__(self):
		return '<Documents_Signatures document_id:%r>' % self.document_id

class Attachment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	template_id = db.Column(db.Integer, ForeignKey('template.id'))
	code= db.Column(db.String(255))
	path= db.Column(db.String(255))
	def __init__(self, template, code, path):
		self.template=template
		self.code=code
		self.path=path
	def __repr__(self):
		return '<Attachment path:%r>' % self.path

class User_Context(db.Model):
	__tablename__ = 'user_context'
	user_id = db.Column(db.Integer, ForeignKey('user.id'), primary_key=True)
	context_id = db.Column(db.Integer, ForeignKey('context.id'), primary_key=True)
	administrator = db.Column(db.Boolean)
	user = db.relationship("User", back_populates="contexts")
	context = db.relationship("Context", back_populates="users")
	def __repr__(self):
		return '<User_Context user_id:%r>' % self.user_id

class Templates_Signatures(db.Model):
	__tablename__ = 'templates_signatures'
	template_id = db.Column(db.Integer, ForeignKey('template.id'), primary_key=True)
	signature_id = db.Column(db.Integer, ForeignKey('signature.id'), primary_key=True)
	signature_order = db.Column(db.Integer)
	authorized = db.Column(db.Integer)
	request_date = db.Column(db.DateTime)
	authorization_date = db.Column(db.DateTime)
	template = db.relationship("Template", back_populates="signatures")
	signature = db.relationship("Signature", back_populates="templates")
	def __init__(self, signature_order):
		self.signature_order=signature_order

	def __repr__(self):
		return '<Templates_Signatures template_id:%r>' % self.template_id

class Notification(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id =  db.Column(db.Integer, db.ForeignKey('user.id'))
	type = db.Column(db.Integer)
	text = db.Column(db.Text)
	viewed = db.Column(db.Boolean)
	def __init__(self, user,type,text):
		self.user=user;
		self.type=type;
		self.text=text;
		self.viewed=False;

	def __repr__(self):
		return '<Notification text:%r>' % self.text

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	author_id =  db.Column(db.Integer, db.ForeignKey('user.id'))
	title = db.Column(db.String(255))
	text = db.Column(db.Text)
	contexts = db.relationship(
		'Post_Context',
		back_populates='post'
	)
	visibility = db.Column(db.Integer) #0 ninguém, 1 departamento, 2 fundacao, 3 publico.
	date = db.Column(db.DateTime, server_default=func.now())
	images = db.relationship('Post_Image', backref='post', lazy='dynamic')
	comments = db.relationship('Post_Comment', backref='post', lazy='dynamic')
	def __init__(self, author, title, text, visibility):
		self.author=author;
		self.title=title;
		self.text=text;
		self.visibility=visibility;
	def __repr__(self):
		return '<Post title:%r>' % self.title

class Context(db.Model):
	__tablename__ = 'context'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	moderated = db.Column(db.Boolean) #0 livre, 1 moderada
	color = db.Column(db.String(7))
	posts = db.relationship(
		'Post_Context',
		back_populates='context'
	)
	users = db.relationship(
		'User_Context',
		back_populates='context'
	)
	def __init__(self, name, color, moderated):
		self.name=name
		self.color=color
		self.moderated=moderated
	def __repr__(self):
		return '<Context name:%r>' % self.name

class Post_Context(db.Model):
	__tablename__ = 'post_context'
	post_id = db.Column(db.Integer, ForeignKey('post.id'), primary_key=True)
	context_id = db.Column(db.Integer, ForeignKey('context.id'), primary_key=True)
	authorized = db.Column(db.Boolean)
	post = db.relationship("Post", back_populates="contexts")
	context = db.relationship("Context", back_populates="posts")
	def __repr__(self):
		return '<Post_Context post_id:%r>' % self.post_id

class Post_Image(db.Model):
	__tablename__ = 'post_image'
	id = db.Column(db.Integer, primary_key=True)
	path = db.Column(db.String(255))
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
	def __init__(self, path, post):
		self.path=path;
		self.post=post;
	def __repr__(self):
		return '<Post_Images path:%r>' % self.path

class Post_Comment(db.Model):
	__tablename__ = 'post_comment'
	id = db.Column(db.Integer, primary_key=True)
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
	parent_id = db.Column(db.Integer, db.ForeignKey('post_comment.id'))
	children = db.relationship('Post_Comment', backref=db.backref('parent', remote_side='Post_Comment.id'), lazy='dynamic')
	text= db.Column(db.Text)
	date = db.Column(db.DateTime, server_default=func.now())
	author_id= db.Column(db.Integer, db.ForeignKey('user.id'))
	def __init__(self, post, parent,text,author):
		self.post=post;
		self.parent=parent;
		self.text=text;
		self.author=author;
	def __repr__(self):
		return '<Post_Comment text:%r>' % self.text

class User_Subscription(db.Model):
	__tablename__ = 'user_subscription'
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	subscription = db.Column(db.String())
	subscriptionhash = db.Column(db.String(), unique=True)
	user = db.relationship("User", back_populates="subscriptions")
	def __init__(self, user, subscription,subscriptionhash):
		self.user=user;
		self.subscription=subscription;
		self.subscriptionhash=subscriptionhash;
	def __repr__(self):
		return '<User_Subscription path:%r>' % self.user_id

class Alumni(db.Model):
	__bind_key__ = 'alumni'
	id = db.Column(db.Integer, primary_key=True)
	curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'))
	cpf = db.Column(db.String(255))
	matricula = db.Column(db.String(255))
	nome = db.Column(db.String(255))
	email = db.Column(db.String(255))
	data_nascimento = db.Column(db.DateTime)
	ano_ingresso = db.Column(db.Integer)
	periodo_ingresso = db.Column(db.Integer)
	data_colacao = db.Column(db.DateTime)
	def __init__(self, cpf, matricula, nome, email, data_nascimento,ano_ingresso,periodo_ingresso,data_colacao,curso):
		self.curso=curso;
		self.cpf=cpf;
		self.matricula=matricula;
		self.nome=nome;
		self.email=email;
		self.data_nascimento=data_nascimento;
		self.ano_ingresso=ano_ingresso;
		self.periodo_ingresso=periodo_ingresso;
		self.data_colacao=data_colacao;
	def __repr__(self):
		return '<Alumni name:%r>' % self.nome

class Curso(db.Model):
	__bind_key__ = 'alumni'
	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(255))
	nivel = db.Column(db.String(255))
	students = db.relationship('Alumni', backref='curso', lazy='dynamic')
	def __init__(self, nome):
		self.nome=nome;
	def __repr__(self):
		return '<Curso nome:%r>' % self.nome

db.create_all();

class unaccent(ReturnTypeFromArgs):
    pass
