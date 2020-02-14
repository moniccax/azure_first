from flask import request, jsonify, render_template, flash, url_for as flask_url_for, Response
from urllib.parse import urlparse, urljoin
from docx import Document as docxDocument
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from docxtpl import DocxTemplate
from subprocess import run
from flask_mail import Mail, Message
from functools import wraps
from settings import *
from operator import attrgetter
from pywebpush import webpush, WebPushException
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging
import time
import os
import io
import zipfile
import hashlib
import random
import pickle
import string
import datetime
import flask
import json
import numpy as np


def url_for(endpoint, **values):
	url = flask_url_for(endpoint, **values);
	if(request.host=="app.fundacaocefetminas.org.br"):
		service=url.split('.')[0].split('/')[2];
		uri= url.split('.br')[1];
		url = "https://app.fundacaocefetminas.org.br/"+service+uri;
	return url;

def get_current_user_role():
	return current_user.category;

def requires_roles(role):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if get_current_user_role() > role:
                return redirect(url_for('admin.index'))
            return f(*args, **kwargs)
        return wrapped
    return wrapper

def allowed_file(filename, extension):
	return '.' in filename and extension in filename

def allowed_file_array(filename, extensions):
	r = False;
	for extension in extensions:
		if extension in filename:
			r=True
	return '.' in filename and r

def swapImages(imglist,docx):
	for img in imglist:
		docx.replace_media(SIGNATURE_EXAMPLES_FOLDER+'/transparent'+str(img.signature_order)+'.png',img.signature.path)

def encrypt_pdf(pdf,outputpdf,code):
	file_writer = PdfFileWriter()
	input_file = PdfFileReader(open(pdf, "rb"))
	page_count = input_file.getNumPages()
	for page_number in range(page_count):
		input_page = input_file.getPage(page_number)
		file_writer.addPage(input_page)
	file_writer.encrypt('',code)
	result_pdf=open(outputpdf,"wb")
	file_writer.write(result_pdf)
	result_pdf.close()

def generatedocument(document):
	docx_document = DocxTemplate(document.template.path)
	i=0
	context = {}
	context["COD"]=document.code;
	anx=False;
	for value in document.values:
			context[value.field.name]=value.value;
			if value.field.name == 'ANEXO':
				anx=True;
			i=i+1;
	signedfile='static/temp/not_encrypted_'+document.template.file_name.replace(".docx", "")+'_'+context["NOME"].replace(" ", "_")+'_'+context["COD"]+'.docx'
	signedpdf='static/temp/not_encrypted_'+document.template.file_name.replace(".docx", "")+'_'+context["NOME"].replace(" ", "_")+'_'+context["COD"]+'.pdf'
	signedattachpdf='static/temp/attach_'+document.template.file_name.replace(".docx", "")+'_'+context["NOME"].replace(" ", "_")+'_'+context["COD"]+'.pdf'
	signedencryptedpdf='static/temp/'+context["NOME"].replace(" ", "_")+'_'+context["COD"]+'.pdf'
	docx_document.render(context)
	imglist=[]
	for temp_signature in document.template.signatures:
		documentsignature=Documents_Signatures.query.filter_by(signature=temp_signature.signature, document=document).first()
		if documentsignature.authorized:
			imglist.append(temp_signature)
	swapImages(imglist,docx_document)
	docx_document.save(signedfile)
	#run(["doc2pdf",signedfile])
	os.system("doc2pdf "+signedfile);
	if anx:
		attachname=context['ANEXO'];
		merger = PdfFileMerger()
		merger.append(PdfFileReader(signedpdf, 'rb'))
		attachment=Attachment.query.filter_by(template=document.template, code=attachname).first();
		if attachment:
			merger.append(PdfFileReader(attachment.path, 'rb'))
		merger.write(signedattachpdf)
		encrypt_pdf(signedattachpdf,signedencryptedpdf,'Docs@Fcm467')
		os.remove(signedattachpdf)
	else:
		encrypt_pdf(signedpdf,signedencryptedpdf,'Docs@Fcm467')
	os.remove(signedpdf)
	os.remove(signedfile)
	return signedencryptedpdf

def filldocuments(template,user):
	start = time.time()
	ziplist=set()
	template_admins=[relationship.user for relationship in template.event.administrators]
	for document in template.documents:
		if user in template_admins:
			for temp_signature in document.template.signatures:
				documentsignature=Documents_Signatures.query.filter_by(signature=temp_signature.signature, document=document).first()
				if not documentsignature.authorized:
					flash("<span>Ainda há assinaturas sem autorização.</span>","red")
					return redirect(url_for('docs.document')+"?template="+str(template.id)+"#template_sign")
			signedencryptedpdf=generatedocument(document)
			ziplist.add(signedencryptedpdf)
	data = io.BytesIO()
	with zipfile.ZipFile(data, mode='w') as z:
		for f_name in ziplist:
			v=f_name.split('/');
			z.write(f_name,v[len(v)-1])
	data.seek(0)
	#for f_name in ziplist:
		#os.remove(f_name)
	end = time.time()
	timer = TimerLog(datetime.timedelta(seconds=(end-start)),2, document.id)
	db.session.add(timer)
	db.session.commit()
	filename=template.event.title+'_'+template.name+'.zip';
	return flask.send_file(
		data,
		mimetype='application/zip',
		as_attachment=True,
		attachment_filename=filename.encode("ascii","replace").decode("ascii"),
		cache_timeout=-1
	)

def filldocument(document,user,viewMode):
	if document.available:
		start = time.time()
		signedencryptedpdf=generatedocument(document)
		f=open(signedencryptedpdf, 'rb')
		os.remove(signedencryptedpdf)
		if user.is_authenticated:
			log=Log(user,"Read",document)
			db.session.add(log)
		end = time.time()
		timer = TimerLog(datetime.timedelta(seconds=(end-start)),1, document.id)
		db.session.add(timer)
		db.session.commit()
		if viewMode == "inline":
			attach=False;
		else:
			attach=True;
		filename=signedencryptedpdf.split('/')[-1];
		try:
			return flask.send_file(f,
	                     attachment_filename=filename.encode("ascii","replace").decode("ascii"),
	                     as_attachment=attach,
	                     mimetype="application/pdf")
		except Exception as e:
			print(str(e))
	else:
		return redirect(url_for('admin.index'))

def filldocumenttest(document,user,viewMode):
	start = time.time()
	signedencryptedpdf=generatedocument(document)
	f=open(signedencryptedpdf, 'rb')
	os.remove(signedencryptedpdf)
	log=Log(user,"Test-Read",document)
	db.session.add(log)
	end = time.time()
	timer = TimerLog(datetime.timedelta(seconds=(end-start)),1, document.id)
	db.session.add(timer)
	db.session.commit()
	if viewMode == "inline":
		attach=False;
	else:
		attach=True;
	filename=signedencryptedpdf.split('/')[-1];
	return flask.send_file(f,
                     attachment_filename=filename.encode("ascii","replace").decode("ascii"),
                     as_attachment=attach,
                     mimetype="application/pdf")


def checkExcelFile(array):
	fields=array[0];
	fieldsNumber=len(fields)
	if fieldsNumber<3:
		return "Número de colunas inconsistente!"
	if fields[0]!="CPF":
		return "Coluna CPF não encontrada!"
	if fields[1]!="NOME":
		return "Coluna NOME não encontrada!"
	if fields[2]!="EMAIL":
		return "Coluna EMAIL não encontrada!"

	values= array[1::]
	i=1;
	for line in values:
		if len(line)!=fieldsNumber:
			return "Inconsistencia na linha "+str(i)+"!";
		if not verifyCpf(line[0]):
			return "CPF invalido na linha "+str(i)+"!";
		i=i+1;
	return 1;

def verifyCpf(cpf):
	if len(cpf)!=14:
		return 0;
	else:
		if cpf[0].isdigit() and cpf[1].isdigit() and cpf[2].isdigit() and cpf[3]=="." and cpf[4].isdigit() and cpf[5].isdigit() and cpf[6].isdigit() and cpf[7]=="." and cpf[8].isdigit() and cpf[9].isdigit() and cpf[10].isdigit() and cpf[11]=="-" and cpf[12].isdigit() and cpf[13].isdigit():
		 	return 1;
	return 0;

def savevalues(array,template,logged,sbr):
	fields=array[0];
	values=array[1::];
	doc=[]
	for line in values:
		usercpf=line[0]
		user=User.query.filter_by(cpf=usercpf).first()
		if user is None:
			user=create_user(line[1], line[0], line[2], hashlib.md5(random_password().encode('utf-8')).hexdigest(),"3000",True,True)
		template.event.users.append(user)
		if sbr == "sbr":
			current=Document.query.filter_by(template=template,user=user).first()
		else:
			current=None
		if current is None:
			current=Document(template,user,0)
			current.code=lcgDocumentCodes()
			log=Log(user,"Post",current)
			if template.signatures is not None:
				for templatesignature in template.signatures:
					temp_sign_toadd=Documents_Signatures()
					temp_sign_toadd.signature=templatesignature.signature
					temp_sign_toadd.document=current
					if templatesignature.signature.user==logged:
						temp_sign_toadd.authorized=1
						temp_sign_toadd.request_date=datetime.datetime.now()
						temp_sign_toadd.authorization_date=datetime.datetime.now()
						if templatesignature.authorized:
							templatesignature.request_date=datetime.datetime.now()
							templatesignature.authorization_date=datetime.datetime.now()
					else:
						temp_sign_toadd.authorized=0
						temp_sign_toadd.request_date=datetime.datetime.now()
						templatesignature.authorized=0
						templatesignature.request_date=datetime.datetime.now()
					db.session.add(temp_sign_toadd)
			db.session.add(log)
			db.session.commit()
		doc.append(current)
	i=0;
	for field in fields:
		toadd_field=Field.query.filter_by(template_id=template.id, name=field).first()
		if toadd_field is None:
			toadd_field= Field(template,field)
		j=0;
		for line in values:
			v = Value.query.filter_by(field=toadd_field, document=doc[j]).first()
			if v is None:
				v = Value(line[i],toadd_field,doc[j])
				db.session.add(v)
			else:
				v.value=line[i]
			db.session.commit()
			j=j+1;
		i=i+1;
	return 1;



def create_user(name, cpf, email, password, category, blocked, locked):
	user=User(name, cpf, email, password,category,1,0)
	user.blocked=blocked;
	user.locked=locked;
	db.session.add(user)
	db.session.commit()
	return user

def random_password():
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8));

def random_token():
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase +string.ascii_lowercase + string.digits) for _ in range(64));

def set_user_token(user):
	token=random_token();
	user.token=token
	user.last_token=datetime.datetime.now();
	db.session.commit()
	return token;

def is_logged(user,token):
	if user.token==token and datetime.datetime.now()-user.last_token<datetime.timedelta(days=2):
		return True;
	return False;

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender = sender, recipients = recipients.split())
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def getNotifications(user):
	notifications = set()
	usersign=user.signature.first()
	documents_to_sign=Documents_Signatures.query.filter_by(signature=usersign,authorized=0)
	templates_to_sign = set()
	for each in documents_to_sign:
		templates_to_sign.add(each.document.template)
	for each in templates_to_sign:
		notifications.add(
		'''
		<a href="'''+url_for('docs.signconfirmation', id=each.id)+'''" style="color: #000">
			<i class="material-icons" style="float: left; margin-right: 3%; margin-top: -0.5%;">border_color</i>
			Solicitação para assinatura em '''+each.name+'''
		</a>
		'''
		)
	notifications_list=Notification.query.filter_by(user=user,viewed=False);
	for each in notifications_list:
		if each.type==1:
			text=each.text.split(";")
			notifications.add(
			'''
				<i class="material-icons" style="float: left; margin-right: 3%; margin-top: -0.5%;">done</i>
				Modelo "'''+text[0]+'''" assinado por '''+text[1]+''' <a href="'''+url_for('docs.dismiss_notification', id=each.id)+'''?previous='''+request.url+'''"> Entendi! </a>
				'''
			)
	return notifications

def getMobileNotifications(user):
	notifications = list()
	usersign=user.signature.first()
	templates_to_sign=Templates_Signatures.query.filter_by(signature=usersign,authorized=0)
	templates=[relationship.template for relationship in templates_to_sign]
	for each in templates:
		admins=[admin_relationship.user for admin_relationship in each.event.administrators];
		s="";
		if len(admins) > 1:
			for i in range(0, len(admins)):
				if i==len(admins)-2:
					s=s+admins[i].name.split(" ")[0]+" e ";
				else:
					s=s+admins[i].name.split(" ")[0]+", ";
		else:
			s=admins[0].name;
		notifications.append(
			"Solicitação de "+s+" para assinatura em " + each.name
		)
	notifications_list=Notification.query.filter_by(user=user,viewed=False);
	for each in notifications_list:
		if each.type==1:
			text=each.text.split(";")
			notifications.append(
			"Modelo "+text[0]+" assinado por "+text[1]
			)
	return Response(json.dumps(notifications),  mimetype='application/json')

def send_notifications(user, text):
	subscriptions=User_Subscription.query.filter_by(user=user)
	for subscription in subscriptions:
		try:
			webpush(subscription_info=json.loads(subscription.subscription),
				data=text,# could be json object as well
				vapid_private_key=WEBPUSH_VAPID_PRIVATE_KEY,
				vapid_claims={
					"sub": "mailto:daniel@fundacaocefetminas.org.br"
				}
			)
		except WebPushException as e:
			logging.exception("webpush fail")


def print_comment(comment,logged):
	s = '''
	<ul class="collapsible" data-collapsible="expandable">
		<li id="comment_'''+str(comment.id)+'''">
			<div class="collapsible-header active">
				<div class="row">
					<div class="col s12">
						<img src="'''+comment.author.getprofilepic()+'''" class="profile_img">
						<font class="ms_medium user_name" color="#787c7e" size="2">
							<p class="p_margin">
								'''+comment.author.name.split(" ")[0]+''' '''+comment.author.name.split(" ")[-1]+'''
							</p>
							<p class="p_margin">
								'''+comment.date.strftime('%d/%m/%Y %H:%M')+'''
							</p>
						</font>'''
	if(logged.is_authenticated and logged==comment.author):
		s+='''
						<div class="fixed-action-btn horizontal click-to-toggle comment_btn">
				            <a class="btn-floating btn-large comment_btn_menu">
				            	<i class="material-icons">more_vert</i>
				            </a>
				            <ul>
								<li>
									<a id="btn_comment_'''+str(comment.id)+'''" class="btn-floating comment_btn_submenu tooltipped" data-position="bottom" data-delay="50" data-tooltip="Comentar">
										<i class="material-icons">comment</i>
									</a>
								</li>
								<li>
									<a href="#modal_edit_comment_btn_'''+str(comment.id)+'''" class="btn-floating modal-trigger comment_btn_submenu tooltipped" data-position="bottom" data-delay="50" data-tooltip="Editar">
										<i class="material-icons">edit</i>
									</a>
								</li>
								<li>
									<a href="#modal_delete_comment_'''+str(comment.id)+'''" class="btn-floating modal-trigger comment_btn_submenu tooltipped" data-position="bottom" data-delay="50" data-tooltip="Excluir">
										<i class="material-icons">delete</i>
									</a>
								</li>
							</ul>
						</div>'''
	elif logged.is_authenticated:
		s+='''
						<a id="btn_comment_'''+str(comment.id)+'''" class="btn-floating btn-large waves-effect waves-light comment_btn_2 tooltipped" data-position="bottom" data-delay="50" data-tooltip="Comentar">
							<i class="material-icons">comment</i>
						</a>
		'''
	s+='''
					</div>
				</div>
				<div class="row text_margin">
					<div class="col s12 m12 l12">
						<font class="ms_regular" color="#000" size="3">
							<p align="justify">
								'''+"<br>".join(comment.text.split("\n"))+'''
							</p>
						</font>
					</div>
				</div>
				<div class="hide" id="new_comment_'''+str(comment.id)+'''">
					<div class="row box_comment">
						<form class="col s12" id="form_comment_'''+str(comment.id)+'''" action="'''+url_for('connect.comment_post', id=comment.id)+'''" method="post">
							<div class="row textarea_comment">
								<div class="input-field s12 m12 l12">
									<textarea id="txt_comment_'''+str(comment.id)+'''" name="txt_comment_'''+str(comment.id)+'''" class="materialize-textarea ms_regular"></textarea>
									<label class="ms_medium" for="txt_comment_'''+str(comment.id)+'''">Escreva um comentário</label>
								</div>
							</div>
							<div class="row">
								<button class="btn waves-effect waves-light send_comment" type="submit">
									Enviar
								</button>
							</div>
						</form>
					</div>
				</div>
			</div>'''

	children=Post_Comment.query.filter_by(parent_id=comment.id).order_by(Post_Comment.date.desc());

	if children.count() > 0:
		s+='''<div class="collapsible-body">''';

	for child in children:
		s+=print_comment(child, logged);

	if children.count() > 0:
		s+='''</div>''';

	s+='''</li></ul>''';

	return s;

def print_comment_ionic(comment,logged):
	root_comments=comment.children;
	s=[];
	for comment in root_comments:
		s.append(print_comment_ionic(comment,logged));
	editable=False;
	if comment.author_id==logged.id:
		editable=True;
	return {"id":comment.id, "author_id":comment.author_id, "author": comment.author.name, "author_profilepic":comment.author.getprofilepic(), "date": comment.date, "text":comment.text, "editable":editable, "children": s}

#Seeds
def lcgTemplatesNames():
	a=161
	c=506903
	m=100000000
	row=Seed.query.filter_by(name='TemplatesNames').first()
	if row is None:
		row=Seed('TemplatesNames',0)
		db.session.add(row)
		db.session.commit()
	num=row.value
	num=(a*num+c)%m
	row.value=num
	db.session.commit()
	return str(num).zfill(8)

def lcgSignaturesNames():
	a=161
	c=506903
	m=100000000
	row=Seed.query.filter_by(name='SignaturesNames').first()
	if row is None:
		row=Seed('SignaturesNames',0)
		db.session.add(row)
		db.session.commit()
	num=row.value
	num=(a*num+c)%m
	row.value=num
	db.session.commit()
	return str(num).zfill(8)

def lcgDocumentCodes():
	a=161
	c=506903
	m=100000000
	row=Seed.query.filter_by(name='DocumentCodes').first()
	if row is None:
		row=Seed('DocumentCodes',0)
		db.session.add(row)
		db.session.commit()
	num=row.value
	num=(a*num+c)%m
	row.value=num
	db.session.commit()
	return str(num).zfill(8)

def lcgPostImagesNames():
	a=161
	c=506903
	m=100000000
	row=Seed.query.filter_by(name='PostImages').first()
	if row is None:
		row=Seed('PostImages',0)
		db.session.add(row)
		db.session.commit()
	num=row.value
	num=(a*num+c)%m
	row.value=num
	db.session.commit()
	return str(num).zfill(8)

def lcgProfilePictureNames():
	a=161
	c=506903
	m=100000000
	row=Seed.query.filter_by(name='SignaturesNames').first()
	if row is None:
		row=Seed('SignaturesNames',0)
		db.session.add(row)
		db.session.commit()
	num=row.value
	num=(a*num+c)%m
	row.value=num
	db.session.commit()
	return str(num).zfill(8)

def lcgAttachmentsNames():
	a=161
	c=506903
	m=100000000
	row=Seed.query.filter_by(name='AttachmentNames').first()
	if row is None:
		row=Seed('AttachmentNames',0)
		db.session.add(row)
		db.session.commit()
	num=row.value
	num=(a*num+c)%m
	row.value=num
	db.session.commit()
	return str(num).zfill(8)

def backup_database():
	start=time.time()
	now = datetime.datetime.now()
	filename=str(now).split('.')[0].replace(" ","_").replace(":","");
	path=BACKUP_FOLDER+"/"+filename
	count = countRows()
	call(["pg_dump", "-U", "docs", "-h", "localhost", "-Fc", "docs", "-f", path])
	end = time.time()
	timer = TimerLog(datetime.timedelta(seconds=(end-start)),3,None,filename)
	db.session.add(timer)
	db.session.commit()
	return count;

def restore_database(file):
	start=time.time()
	db.session.close()
	path=BACKUP_FOLDER+"/"+file;
	call(["pg_restore", "-c", "-U", "docs", "-h", "localhost", "-d", "docs", path])
	count = countRows()
	end = time.time()
	timer = TimerLog(datetime.timedelta(seconds=(end-start)),4, None,file)
	db.session.add(timer)
	db.session.commit()
	return count;

def countRows():
	count=User.query.filter_by().count();
	count+=Template.query.filter_by().count();
	count+=Event.query.filter_by().count();
	count+=Field.query.filter_by().count();
	count+=Seed.query.filter_by().count();
	count+=Log.query.filter_by().count();
	count+=Document.query.filter_by().count();
	count+=Value.query.filter_by().count();
	count+=Signature.query.filter_by().count();
	count+=Documents_Signatures.query.filter_by().count();
	count+=Templates_Signatures.query.filter_by().count();
	return count;

def verifyMaintenance(logged,system,ret):
	setting=Systemsettings.query.filter_by(key="maintenance").first()
	if setting.value=="true" and logged and logged.category>=2000:
		return redirect(url_for('admin.maintenance'));
	else:
		keyquery="maintenance-"+system
		setting=Systemsettings.query.filter_by(key=keyquery).first()
		if setting.value=="true" and logged and logged.category>=2000:
			return redirect(url_for('admin.maintenance'));
		else:
			return ret;
	#if logged.category<3:
		#return redirect(url_for('admin.maintenance'));
	#else:
		#return ret;
	#return redirect('/')

def unlock_document_list(documents, session):
	atLeastOneAvailable=0;
	allAvailable=1;
	for doc in documents:
		if not doc.available:
			doc.available=1;
			for sig in doc.signatures:
				if not(sig.authorized):
					doc.available=0;
					allAvailable=0;
			if doc.available:
				atLeastOneAvailable=1;
				if doc.user.locked:
					password=random_password()
					doc.user.password=hashlib.md5(password.encode('utf-8')).hexdigest()
					email_content("unlock_document_list",doc.user,password)
					doc.user.locked=False;
					doc.user.blocked=False;
				else:
					email_content("unlock_document_list_2",doc.user,doc)

		session.commit()
	if allAvailable:
		return 2
	else:
		if atLeastOneAvailable:
			return 1
		else:
			return 0

def export_xlsx(template):
	fields=Field.query.filter_by(template_id=template.id)
	documents=Document.query.filter_by(template_id=template.id)
	j=0;
	csv=[];
	lines=[];
	lines.append([]);
	for field in fields:
		lines[0].append(field.name)
		i=1;
		for document in documents:
			value=Value.query.filter_by(document_id=document.id, field_id=field.id).first()
			if j==0:
				lines.append([]);
			lines[i].append(str(value.value))
			i=i+1;
		j=1;
	filename=template.name.replace(" ","")+".xlsx"
	return excel.make_response_from_array(lines, "xlsx",file_name=filename)

def createRow(user): #create row to be saved in sheet for an product
	#certify every key has a value
	print("creating row for user "+str(user['name']));
	if not 'name' in user:
		user['name']="";
	if not 'tel' in user:
		user['tel']="";
	#create values row
	values = [
		[
			user['name'],
			user['tel'],
			datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
		]
	];
	print("success!");
	return values;

def createRowDenuncia(msg): #create row to be saved in sheet for an product
	#certify every key has a value
	print("creating row for message "+str(msg['Id']));
	if not 'Id' in msg:
		msg['Id']="";
	if not 'nome' in msg:
		msg['nome']="";
	if not 'email' in msg:
		msg['email']="";
	if not 'ip' in msg:
		msg['ip']="";
	if not 'message' in msg:
		msg['message']="";
	#create values row
	values = [
		[
			msg['Id'],
			msg['nome'],
			msg['email'],
			msg['message'],
			msg['ip'],
			datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
		]
	];
	print("success!");
	return values;

def createRowFormInteresse(user):
	print("creating row for user "+str(user['nome']));
	if not 'nome' in user:
		user['nome']="";
	if not 'email' in user:
		user['email']="";
	if not 'tel' in user:
		user['tel']="";
	if not 'idioma' in user:
		user['idioma']="";
	if not 'experiencia' in user:
		user['experiencia']="";
	values = [
		[
			user['nome'],
			user['email'],
			user['tel'],
			user['idioma'],
			user['experiencia'],
			datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
		]
	];
	return values;

def createRowFormTermoConcursos(termo):
	print("creating row for termo "+str(termo['NOME']));
	if not 'NOME' in termo:
		termo['NOME']=''
	if not 'AREA' in termo:
		termo['AREA']=''
	if not 'CAMP' in termo:
		termo['CAMP']=''
	if not 'FUNCAO' in termo:
		termo['FUNCAO']=''
	if not 'VINCULO' in termo:
		termo['VINCULO']=''
	if not 'TITULACAO' in termo:
		termo['TITULACAO']=''
	if not 'FORMACAO' in termo:
		termo['FORMACAO']=''
	if not 'DATANASC' in termo:
		termo['DATANASC']=''
	if not 'RG' in termo:
		termo['RG']=''
	if not 'ORGEXP' in termo:
		termo['ORGEXP']=''
	if not 'CPF' in termo:
		termo['CPF']=''
	if not 'MATRICULA' in termo:
		termo['MATRICULA']=''
	if not 'PIS' in termo:
		termo['PIS']=''
	if not 'ENDERECO' in termo:
		termo['ENDERECO']=''
	if not 'BAIRRO' in termo:
		termo['BAIRRO']=''
	if not 'MUNICIPIO' in termo:
		termo['MUNICIPIO']=''
	if not 'UF' in termo:
		termo['UF']=''
	if not 'CEP' in termo:
		termo['CEP']=''
	if not 'CEL1' in termo:
		termo['CEL1']=''
	if not 'CEL2' in termo:
		termo['CEL2']=''
	if not 'TEL1' in termo:
		termo['TEL1']=''
	if not 'TEL2' in termo:
		termo['TEL2']=''
	if not 'EMAIL' in termo:
		termo['EMAIL']=''
	if not 'ESTADOCIVIL' in termo:
		termo['ESTADOCIVIL']=''
	if not 'BANCO' in termo:
		termo['BANCO']=''
	if not 'NBANCO' in termo:
		termo['NBANCO']=''
	if not 'AGENCIA' in termo:
		termo['AGENCIA']=''
	if not 'CONTA' in termo:
		termo['CONTA']=''
	if not 'TIPOCONTA' in termo:
		termo['TIPOCONTA']=''
	if not 'CONJUNTA' in termo:
		termo['CONJUNTA']=''
	if not 'CORRENTISTA2' in termo:
		termo['CORRENTISTA2']=''
	if not 'TIPOPAGAMENTO' in termo:
		termo['TIPOPAGAMENTO']=''
	values = [
		[
			termo['NOME'],
			termo['AREA'],
			termo['CAMP'],
			termo['FUNCAO'],
			termo['VINCULO'],
			termo['TITULACAO'],
			termo['FORMACAO'],
			termo['DATANASC'],
			termo['RG'],
			termo['ORGEXP'],
			termo['CPF'],
			termo['MATRICULA'],
			termo['PIS'],
			termo['ENDERECO'],
			termo['BAIRRO'],
			termo['MUNICIPIO'],
			termo['UF'],
			termo['CEP'],
			termo['CEL1'],
			termo['CEL2'],
			termo['TEL1'],
			termo['TEL2'],
			termo['EMAIL'],
			termo['ESTADOCIVIL'],
			termo['BANCO'],
			termo['NBANCO'],
			termo['AGENCIA'],
			termo['CONTA'],
			termo['TIPOCONTA'],
			termo['CONJUNTA'],
			termo['CORRENTISTA2'],
			termo['TIPOPAGAMENTO']
		]
	];
	return values;

def createRowForFormularioConcursos(termo):
	print("creating row for formulario "+str(termo['NOME']));
	if not 'NOME' in termo:
		termo['NOME']=''
	if not 'AREA' in termo:
		termo['AREA']=''
	if not 'FUNCAO' in termo:
		termo['FUNCAO']=''
	if not 'VINCULO' in termo:
		termo['VINCULO']=''
	if not 'ENDERECO' in termo:
		termo['ENDERECO']=''
	if not 'BAIRRO' in termo:
		termo['BAIRRO']=''
	if not 'MUNICIPIO' in termo:
		termo['MUNICIPIO']=''
	if not 'UF' in termo:
		termo['UF']=''
	if not 'CEP' in termo:
		termo['CEP']=''
	if not 'DESLOCAMENTO_OD' in termo:
		termo['DESLOCAMENTO_OD']=''
	if not 'DESLOCAMENTO-AUX' in termo:
		termo['DESLOCAMENTO-AUX']=''
	if not 'TRANSLADO' in termo:
		termo['TRANSLADO']=''
	if not 'HOSPEDAGEM' in termo:
		termo['HOSPEDAGEM']=''
	if not 'HOSPEDAGEM-AUX' in termo:
		termo['HOSPEDAGEM-AUX']=''
	if not 'ALIMENTACAO' in termo:
		termo['ALIMENTACAO']=''
	if not 'DATANASC' in termo:
		termo['DATANASC']=''
	if not 'CPF' in termo:
		termo['CPF']=''
	if not 'RG' in termo:
		termo['RG']=''
	if not 'ORGEXP' in termo:
		termo['ORGEXP']=''
	if not 'ESTADOCIVIL' in termo:
		termo['ESTADOCIVIL']=''
	if not 'CEL1' in termo:
		termo['CEL1']=''
	if not 'EMAIL' in termo:
		termo['EMAIL']=''
	if not 'BANCO' in termo:
		termo['BANCO']=''
	if not 'NBANCO' in termo:
		termo['NBANCO']=''
	if not 'AGENCIA' in termo:
		termo['AGENCIA']=''
	if not 'CONTA' in termo:
		termo['CONTA']=''
	if not 'TIPOCONTA' in termo:
		termo['TIPOCONTA']=''
	if not 'CONJUNTA' in termo:
		termo['CONJUNTA']=''
	if not 'CORRENTISTA2' in termo:
		termo['CORRENTISTA2']=''
	values = [
		[
			termo['NOME'],
			termo['AREA'],
			termo['FUNCAO'],
			termo['VINCULO'],
			termo['ENDERECO'],
			termo['BAIRRO'],
			termo['MUNICIPIO'],
			termo['UF'],
			termo['CEP'],
			termo['DESLOCAMENTO_OD'],
			termo['DESLOCAMENTO-AUX'],
			termo['TRANSLADO'],
			termo['HOSPEDAGEM'],
			termo['HOSPEDAGEM-AUX'],
			termo['ALIMENTACAO'],
			termo['DATANASC'],
			termo['CPF'],
			termo['RG'],
			termo['ORGEXP'],
			termo['ESTADOCIVIL'],
			termo['CEL1'],
			termo['EMAIL'],
			termo['BANCO'],
			termo['NBANCO'],
			termo['AGENCIA'],
			termo['TIPOCONTA'],
			termo['CONJUNTA'],
			termo['CONTA'],
			termo['CORRENTISTA2']
		]
	];
	return values;

def saveTermoConcursos(context):
	# If modifying these scopes, delete the file token.pickle.
	SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

	# The ID and range of a sample spreadsheet.
	SPREADSHEET_ID = '1q6wGY_PNkduIZTNzqIw3oNLchJjiC05WQvHCJ6zb4XE' #spreadsheet ID
	print("autheticating")
	creds = None
	# The file token.pickle stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists('token.pickle'):
		with open('token.pickle', 'rb') as token:
			creds = pickle.load(token)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
			creds = flow.run_local_server()
		# Save the credentials for the next run
		with open('token.pickle', 'wb') as token:
			pickle.dump(creds, token)

	service = build('sheets', 'v4', credentials=creds)
	print("authenticated")
	print("reading spreadsheet")
	# Call the Sheets API
	sheet = service.spreadsheets()
	values=createRowFormTermoConcursos(context) #create the line for the sheet
	body = {
		'values': values
	}
	#asks googlesheets API to append the line on sheet "Página1", simulating user entered values. (valueInputOption can be USER_ENTERED or RAW)
	result = service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range='termo', valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body=body).execute()

def saveFormularioConcursos(context):
	# If modifying these scopes, delete the file token.pickle.
	SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

	# The ID and range of a sample spreadsheet.
	SPREADSHEET_ID = '1M0hI0IRp4V7AaZzjaMrBRK0yO_tqTGo-vuNuG6Mi7tE' #spreadsheet ID
	print("autheticating")
	creds = None
	# The file token.pickle stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	if os.path.exists('token.pickle'):
		with open('token.pickle', 'rb') as token:
			creds = pickle.load(token)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
			creds = flow.run_local_server()
		# Save the credentials for the next run
		with open('token.pickle', 'wb') as token:
			pickle.dump(creds, token)

	service = build('sheets', 'v4', credentials=creds)
	print("authenticated")
	print("reading spreadsheet")
	# Call the Sheets API
	sheet = service.spreadsheets()
	values=createRowForFormularioConcursos(context) #create the line for the sheet
	body = {
		'values': values
	}
	#asks googlesheets API to append the line on sheet "Página1", simulating user entered values. (valueInputOption can be USER_ENTERED or RAW)
	result = service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range='termo', valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body=body).execute()

def email_content(content,user,generic=None, generic2=None):
	if content == "forgot_password":
		subject = "Redefinição de Senha"
		msg = '''Prezado(a) ''' + user.name.split(" ")[0] + ''',<br><br>
			Foi solicitada, a redefinição de sua senha de acesso aos sistemas da Fundação CEFETMINAS.<br>
			Utilize o código abaixo para confirmar a solicitação através do link: <a href="http://admin.fundacaocefetminas.org.br/codigo_senha">http://admin.fundacaocefetminas.org.br/codigo_senha</a>.
			<ul>
			<li>Código: <b>'''+user.security_code+'''</b></li>
			</ul>
			Caso não tenha solicitado a redefinição de senha, este e-mail pode ser ignorado.<br><br>
			Atenciosamente,<br><br>
			Fundação CEFETMINAS.<br><br>
			<b>E-mail automático. Por favor não responda.<br>
			Em caso de dúvidas, entre em contato pelo endereço: suporte@fundacaocefetminas.org.br</b>'''

	elif content == "code_confirmation" or content == "reset_password":
		subject = "Redefinição de Senha"
		msg = '''Prezado(a) ''' + user.name.split(" ")[0] + ''',<br><br>
			A sua senha de acesso aos sistemas da Fundação CEFETMINAS foi redefinida recentemente.<br>
			<ul>
			<li>Nova senha: <b>'''+generic+'''</b></li>
			</ul>
			<a href="http://admin.fundacaocefetminas.org.br/login">Clique aqui</a> para entrar.
			<br><br>
			Atenciosamente,<br><br>
			Fundação CEFETMINAS.<br><br>
			<b>E-mail automático. Por favor não responda.<br>
			Em caso de dúvidas, entre em contato pelo endereço: suporte@fundacaocefetminas.org.br</b>'''

	elif content == "create_employee":
		subject = "Confirmação de Cadastro"
		msg = '''Prezado(a) ''' + user.name.split(" ")[0] + ''',<br><br>
			Foi criada uma conta de usuário para este e-mail nos sistemas da Fundação CEFETMINAS.<br>
			A senha disponibilizada é provisória, portanto, você deve alterá-la no primeiro acesso.<br>
			<ul>
			<li>Nome: <b>'''+user.name+'''</b></li>
			<li>CPF: <b>'''+user.cpf+'''</b></li>
			<li>Senha provisória: <b>'''+generic+'''</b></li>
			</ul>
			<a href="http://admin.fundacaocefetminas.org.br/login">http://admin.fundacaocefetminas.org.br/login</a><br><br>
			Atenciosamente,<br><br>
			Fundação CEFETMINAS.<br><br>
			<b>E-mail automático. Por favor não responda.<br>
			Em caso de dúvidas, entre em contato pelo endereço: suporte@fundacaocefetminas.org.br</b><b>Não responda este E-mail</b>'''

	elif content == "add_event_administrator":
		send_notifications(user, "Você agora é um(a) administrador(a) do evento " + generic.title);
		subject = "Adição de Administrador"
		msg = '''Prezado(a) ''' + user.name.split(" ")[0] + ''',<br><br>
			Você agora é um(a) administrador(a) do evento "''' + generic.title + '''", disponível no <a href="http://admin.fundacaocefetminas.org.br/login">Sistema de Gestão de Documentos da FCM</a>.<br><br>
		    Detalhes:
		    <ul>
			<li>Título: <b>''' + generic.title + '''</b></li>
			<li>Resumo: <b>'''+ generic.abstract + '''</b></li>
			</ul>
			Atenciosamente,<br><br>
			Fundação CEFETMINAS.<br><br>
			<b>E-mail automático. Por favor não responda.<br>
			Em caso de dúvidas, entre em contato pelo endereço: suporte@fundacaocefetminas.org.br</b>'''

	elif content == "unlock_document_list":
		subject = "Confirmação de Cadastro"
		msg = '''Prezado(a) ''' + user.name.split(" ")[0] + ''',<br><br>
			Foi criada uma conta de usuário para este e-mail nos <a href="http://admin.fundacaocefetminas.org.br/login">sistemas da Fundação CEFETMINAS</a>.<br>
			A senha disponibilizada é provisória, portanto, você deve alterá-la no primeiro acesso.<br>
			<ul>
			<li>Nome: <b>'''+user.name+'''</b></li>
			<li>CPF: <b>'''+user.cpf+'''</b></li>
			<li>Senha provisória: <b>'''+generic+'''</b></li>
			</ul>
			Atenciosamente,<br><br>
			Fundação CEFETMINAS.<br><br>
			<b>E-mail automático. Por favor não responda.<br>
			Em caso de dúvidas, entre em contato pelo endereço: suporte@fundacaocefetminas.org.br</b>'''

	elif content ==  "unlock_document_list_2":
		send_notifications(user,"Você possui um novo documento disponível");
		subject = "Novo Documento"
		msg = '''Prezado(a) ''' + user.name.split(" ")[0] + ''',<br><br>
		    Você possui um novo documento disponível no <a href="http://admin.fundacaocefetminas.org.br/login">Sistema de Gestão de Documentos da FCM</a>.<br><br>
		    Detalhes:
		    <ul>
			<li>Nome: <b>''' + generic.template.name + '''</b></li>
			<li>Descrição: <b>'''+ generic.template.description + '''</b></li>
			</ul>
			Atenciosamente,<br><br>
			Fundação CEFETMINAS.<br><br>
			<b>E-mail automático. Por favor não responda.<br>
			Em caso de dúvidas, entre em contato pelo endereço: suporte@fundacaocefetminas.org.br</b>'''

	elif content == "add_sign":
		send_notifications(user,"Sua assinatura foi solicitada!");
		subject = "Solicitação de Assinatura"
		msg = '''Prezado(a) ''' + user.name.split(" ")[0] + ''',<br><br>
			Os colaboradores:<br><ul>''';
		for admin in generic.event.administrators:
			msg+="<li>"+admin.user.name+"</li>";
		msg+= '''</ul> estão solicitando a sua assinatura no modelo "''' + generic.name + '''". <br>
			Por favor, acesse o <a href="http://admin.fundacaocefetminas.org.br/login">Sistema de Gestão de Documentos da FCM</a> e verifique essa solicitação.<br><br>
			Atenciosamente,<br><br>
			Fundação CEFETMINAS.<br><br>
			<b>E-mail automático. Por favor não responda.<br>
			Em caso de dúvidas, entre em contato pelo endereço: suporte@fundacaocefetminas.org.br</b>'''

	elif content == "signconfirmation":
		send_notifications(user,"O(a) colaborador(a) "+ generic2.name + " assinou o modelo "+ generic.name);
		subject = "Confirmação de Assinatura"
		msg = '''Prezado(a) ''' + user.name + ''',<br><br>
			O(a) colaborador(a) ''' + generic2.name + ''' assinou o modelo "''' + generic.name + '''".<br><br>
			Atenciosamente,<br><br>
			Fundação CEFETMINAS.<br><br>
			<b>E-mail automático. Por favor não responda.<br>
			Em caso de dúvidas, entre em contato pelo endereço: suporte@fundacaocefetminas.org.br</b>'''


	send_email(subject, "fcm_documentos@fundacaocefetminas.org.br", user.email, "", msg)



#mail--------------------------------------------------------

"""def configure_mail(application):
	# EMAIL SETTINGS
	global mail
	application.config.update(
		MAIL_SERVER = 'smtp.gmail.com',
		MAIL_PORT = 465,
		MAIL_USE_SSL = True,
		MAIL_USERNAME = 'smtp@fundacaocefetminas.org.br',
		MAIL_PASSWORD = 'smtp@Fcm',
		DEFAULT_MAIL_SENDER = 'smtp@gmail.com',
		SECRET_KEY = '9bc3819243c6949d1ae119b8d2cac52c',
	)
	mail=Mail(application)

mail = None
configure_mail(application)"""


#mail--------------------------------------------------------

def configure_mail(application):
	# EMAIL SETTINGS
	global mail
	application.config.update(
		MAIL_SERVER = 'smtp.gmail.com',
		MAIL_PORT = 465,
		MAIL_USE_SSL = True,
		MAIL_USERNAME = 'fcm_documentos@fundacaocefetminas.org.br',
		MAIL_PASSWORD = 'Fcm@Email467',
		DEFAULT_MAIL_SENDER = 'smtp@gmail.com',
		SECRET_KEY = '9bc3819243c6949d1ae119b8d2cac52c',
	)
	mail=Mail(application)

mail = None
configure_mail(application)



@login.user_loader
def load_user(id):
    return User.query.get(int(id))

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def checkaccess(relationship, user): #retorna 0 se invisivel, 1 se visivel, 2 se visivel e editavel
	if user and user.is_authenticated:
		#posts de autoria do usuario
		if relationship.post.author==user:
			return 2;
		#posts pertencentes a contextos administrados pelo usuario
		user_admin_relationship=User_Context.query.filter_by(user=user,administrator=True)
		user_admin=[admin_context.context for admin_context in user_admin_relationship]
		if relationship.context in user_admin:
			return 2;
		#posts restritos a fundacao e usuarios colaboradores
		if relationship.post.visibility==2 and relationship.authorized and user.category<=2000:
			return 1;
		#posts publicos e autorizados
		if relationship.post.visibility>2 and relationship.authorized:
			return 1;
		#posts restritos ao contexto e usuario pertencente ao contexto
		user_contexts = [user_context.context for user_context in user.contexts]
		if relationship.post.visibility==1 and relationship.authorized:
				if relationship.context in user_contexts:
					return 1;
	else:
		if relationship.post.visibility>=3 and relationship.authorized:
			return 1;
	return 0;

@application.context_processor
def utility_processor():
	def getprofilepic(user):
		return User.query.filter_by(id=user).first().getprofilepic()
	def getlastcomment(post):
		comments= Post_Comment.query.filter_by(post=post);
		comments=sorted(comments, key=attrgetter('date'), reverse=True)
		if len(comments) > 0:
			return comments[0];
		else:
			return None;
	def iscontextadmin(user,context):
		for relationship in context.users:
			if relationship.administrator and relationship.user==user:
				return True
		return False
	def iscontextsadmin(user,contexts):
		for context in contexts:
			if iscontextadmin(user, context.context)  and not context.authorized:
				return True
		return False
	return dict(getprofilepic=getprofilepic, getlastcomment=getlastcomment, iscontextadmin=iscontextadmin, iscontextsadmin=iscontextsadmin)
