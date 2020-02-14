from flask import Blueprint, render_template,request, flash, url_for as flask_url_for, send_from_directory
from utils import *
import hashlib

docs = Blueprint('docs', __name__,
                        template_folder='templates', static_folder='../static')

def url_for(endpoint, **values):
	url = flask_url_for(endpoint, **values);
	if(request.host=="app.fundacaocefetminas.org.br"):
		service=url.split('.')[0].split('/')[2];
		uri= url.split('.br')[1];
		url = "https://app.fundacaocefetminas.org.br/"+service+uri;
	return url;

@docs.route('/')
@login_required
def index():
	return redirect(url_for('admin.index'))

# TUTORIAL - tutorial.html

@docs.route('/tutorial', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def tutorial():
	logged=current_user
	output=getNotifications(logged)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'docs', render_template('tutorial.html', user=logged, notifications=output,maintenance=maintenance))


# EVENTOS - events.html

@docs.route('/eventos', methods = ['GET', 'POST'])
@login_required
def events():
	logged=current_user
	documents=Document.query.filter_by(user_id=logged.id, available=True)
	events=set()
	for document in documents:
		events.add(document.template.event)
	output=getNotifications(logged)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	events_own=[event_own.event for event_own in logged.events_own]
	return verifyMaintenance(logged, 'docs',render_template('events.html', events=events, events_own=events_own, user=logged, notifications=output,maintenance=maintenance))


@docs.route('/eventos/criar', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def create_event():
	logged=current_user
	title=request.form['title']
	coordinator=request.form['coordinator']
	abstract=request.form['abstract']
	startDate=request.form['startDate']
	endDate=request.form['endDate']
	workload=request.form['workload']
	place=request.form['place']
	participantsNumber=request.form['participantsNumber']
	if participantsNumber == '':
		participantsNumber=0
	toadd=Event(title, coordinator, abstract, startDate, endDate, workload, place, participantsNumber)
	toadd_relationship=Event_Administrator(logged,toadd)
	db.session.add(toadd)
	db.session.add(toadd_relationship)
	db.session.commit()
	flash('<span>Evento cadastrado com sucesso!</span>','green')
	return redirect(url_for('docs.events'))


@docs.route('/eventos/excluir/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def delete_event(id=None):
	logged=current_user
	if id:
		event=Event.query.filter_by(id=id).first()
		event.users=[];
		if not event.templates.count():
			Event_Administrator.query.filter_by(event=event).delete()
			db.session.delete(event)
			db.session.commit()
			flash('<span>Evento excluído com sucesso!</span>','green')
		else:
			flash('<span>Ainda há modelos cadastrados para este evento.</span>','red')
	return redirect(url_for('docs.events'))


# MODELOS - templates.html

@docs.route('/modelos/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def templates(id=None):
	logged=current_user
	if id:
		event=Event.query.filter_by(id=id).first()
		templates=Template.query.filter_by(event=event)
		employeeUsers=User.query.filter(User.category<2250)
		employeeUsers=sorted(employeeUsers, key=lambda user: user.name)
		output=getNotifications(logged)
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
			return verifyMaintenance(logged, 'docs', render_template('templates.html', templates=templates, event_id=id, event=event, event_administrators=event_administrators, user=logged, employeeUsers=employeeUsers, notifications=output,maintenance=maintenance))
	return redirect(url_for('admin.login'))


@docs.route('/modelos/eventos/atualizar/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def templates_update_event(id=None):
	logged=current_user
	if id:
		event=Event.query.filter_by(id=id).first()
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			title=request.form['title']
			coordinator=request.form['coordinator']
			place=request.form['place']
			abstract=request.form['abstract']
			startDate=request.form['startDate']
			endDate=request.form['endDate']
			workload=request.form['workload']
			participantsNumber=request.form['participantsNumber']
			if participantsNumber == '':
				participantsNumber=0
			event.title=title
			event.coordinator=coordinator
			event.place=place
			event.abstract=abstract
			event.startDate=startDate
			event.endDate=endDate
			event.workload=workload
			event.participantsNumber=participantsNumber
			db.session.commit()
			flash('<span>Evento atualizado com sucesso!</span>','green')
			return redirect(url_for('docs.templates',id=str(id))+"#event_details")
	return redirect(url_for('admin.login'))


@docs.route('/modelos/adicionar_administrador/<uid>/<eid>', methods=['GET', 'POST'])
@login_required
@requires_roles(2250)
def add_administrator(uid=None, eid=None):
	logged=current_user
	if uid and eid:
		user=User.query.filter_by(id=uid).first()
		event=Event.query.filter_by(id=eid).first()
		event_adm = Event_Administrator.query.filter_by(user=user, event=event).first()
		if event_adm is not None:
			return jsonify(success=False, message='<span>'+user.name+' já é um(a) administrator(a) do evento.</span>',color='red')
		else:
			toadd = Event_Administrator(user, event)
			db.session.add(toadd)
			db.session.commit()
			email_content("add_event_administrator",user,event)
			return jsonify(success=True, message='<span>'+user.name+' adicionado(a) com sucesso!</span>',color='green')
	return redirect(url_for('admin.login'))


@docs.route('/modelos/remover_administrador/<uid>/<eid>', methods=['GET', 'POST'])
@login_required
@requires_roles(2250)
def remove_administrator(uid=None, eid=None):
	logged=current_user
	if uid and eid:
		user=User.query.filter_by(id=uid).first()
		event=Event.query.filter_by(id=eid).first()
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if len(event_administrators) > 1:
			Event_Administrator.query.filter_by(user=user, event=event).delete()
			db.session.commit()
			if user==logged:
				return jsonify(success=False, message='removido-'+event.title,color='red')
			return jsonify(success=True, message='<span>'+user.name+' removido(a) com sucesso!</span>',color='green')
		else:
			return jsonify(success=False, message='<span>Não é possivel deixar o evento sem administradores.</span>',color='red')
	return redirect(url_for('admin.login'))


@docs.route('/modelos/criar/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def create_template(id=None):
	logged=current_user
	if id:
		event=Event.query.filter_by(id=id).first()
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			name=request.form['name']
			description=request.form['description']
			file=request.files.get('file')
			if file and allowed_file(file.filename, "docx"):
				fileName=file.filename;
				newFileName=lcgTemplatesNames()+".docx";
				file.save(TEMPLATE_UPLOAD_FOLDER+"/"+newFileName);
				toadd = Template(name, description,TEMPLATE_UPLOAD_FOLDER+"/"+newFileName,event,fileName);
				db.session.add(toadd);
				db.session.commit();
				flash('<span>Modelo cadastrado com sucesso!</span>','green');
			return redirect(url_for('docs.templates',id=str(id))+"#event_templates");
	return redirect(url_for('admin.login'))


@docs.route('/modelos/excluir/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def delete_template(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			document=Document.query.filter_by(template_id=id).first()
			eventid=template.event.id
			if document is None:
				Templates_Signatures.query.filter_by(template_id=id).delete()
				Documents_Signatures.query.filter(Documents_Signatures.document.has(Document.template_id==int(id))).delete(synchronize_session=False)
				os.remove(template.path)
				Attachments = Attachment.query.filter_by(template_id=id)
				for attach in Attachments:
					os.remove(attach.path)
				Attachment.query.filter_by(template_id=id).delete()
				Field.query.filter_by(template_id=id).delete()
				Template.query.filter_by(id=id).delete()
				db.session.commit()
				flash('<span>Modelo excluído com sucesso!</span>','green')
			else:
				flash('<span>Existem documentos cadastrados para este modelo.</span>','red')
		return redirect(url_for('docs.templates',id=eventid)+"#event_templates")
	return redirect(url_for('admin.login'))


# DOCUMENTOS - document.html

@docs.route('/disponibilizar_documentos/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def document(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		output=getNotifications(logged)
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			fields=Field.query.filter_by(template_id=id)
			documents=Document.query.filter_by(template_id=id)
			j=0;
			r=[];
			for field in fields:
				i=0;
				for document in documents:
					value=Value.query.filter_by(document_id=document.id, field_id=field.id).first()
					if value is not None:
						if len(r)<=i:
							r.append([])
						r[i].append(value)
						i=i+1;
			maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
			signatures=Signature.query
			userList=[signature.user for signature in signatures]
			userList=sorted(userList, key=lambda user: user.name)
			return verifyMaintenance(logged, 'docs',render_template('document.html', template=template, user=logged, template_id=template.id, event_id=template.event.id, notifications=output, table=r, maintenance=maintenance, userList=userList))
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/modelos/atualizar/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def documents_update_template(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			name=request.form['name']
			description=request.form['description']
			template.name=name
			template.description=description
			file=request.files.get('file')
			if file and allowed_file(file.filename, "docx"):
				os.remove(template.path)
				template.file_name=file.filename;
				file.save(template.path)
			db.session.commit()
			flash('<span>Modelo atualizado com sucesso!</span>','green')
			return redirect(url_for('docs.document', id=str(id))+"#template_details")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/anexos/adicionar/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def add_attachment(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			code=request.form['name']
			file=request.files.get('file')
			if file and allowed_file(file.filename, "pdf"):
				newFileName=lcgAttachmentsNames()+".pdf";
				path=ATTACHMENT_UPLOAD_FOLDER+"/"+newFileName
				file.save(path);
				toadd= Attachment(template, code, path)
				db.session.add(toadd)
				db.session.commit()
				flash('<span>Anexo adicionado com sucesso!</span>','green')
			else:
				flash('<span>O anexo deve ser um pdf.</span>','red')
			return redirect(url_for('docs.document', id=str(id))+"#template_attachment")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/anexos/remover/<aid>/<tid>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def remove_attachment(aid=None, tid=None):
	logged=current_user
	if aid and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			toremove= Attachment.query.filter_by(id=aid).first()
			if toremove:
				os.remove(toremove.path)
				db.session.delete(toremove)
				db.session.commit()
				flash('<span>Anexo removido com sucesso!</span>','green')
			else:
				flash('<span>Anexo não encontrado.</span>','red')
			return redirect(url_for('docs.document', id=str(tid))+"#template_attachment")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/adicionar_participantes/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def upload_participants(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			array=request.get_array(field_name='file',encoding='latin1',library='pyexcel-xlsxr',auto_detect_float=False,auto_detect_int=False)
			sbr_table=request.form['sbr_table']
			check=checkExcelFile(array);
			if check==1:
				if(savevalues(array,template,logged, sbr_table)==1):
					flash('<span>Participantes adicionados com sucesso!</span>','green')
					return redirect(url_for('docs.document', id=str(id))+"#template_documents")
				else:
					flash('<span>Ocorreu um erro ao adicionar participantes.</span>','red')
			else:
				flash('<span>'+check+' Verifique o <a class="toast_link" href='+url_for('docs.tutorial')+'>tutorial</a>.</span>','red')
			return redirect(url_for('docs.document', id=str(id))+"#template_documents")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/excluir_participantes/<did>/<tid>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def delete_participants(did=None, tid=None):
	logged=current_user
	if did and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			Value.query.filter_by(document_id=int(did)).delete()
			document=Document.query.filter_by(id=int(did)).first()
			Documents_Signatures.query.filter_by(document_id=int(did)).delete()
			db.session.delete(document)
			if template.documents.count() == 0:
				Value.query.filter(Value.field.has(Field.template_id==int(tid))).delete(synchronize_session=False)
				Field.query.filter_by(template_id=int(tid)).delete()
			db.session.commit()
			flash('<span>Participante excluído com sucesso!</span>','green')
			return redirect(url_for('docs.document', id=str(tid))+"#template_documents")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/adicionar_assinatura/<id>', methods = ['POST'])
@login_required
@requires_roles(2250)
def add_sign(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			cpfsign=request.form['cpf_sign'];
			color_sign=request.form['color_sign']
			assinante=User.query.filter_by(cpf=cpfsign).first()
			sign_order=Templates_Signatures.query.filter_by(signature_order=color_sign, template_id=id).first()
			if sign_order is not None:
				flash('<span>Você não pode adicionar duas assinaturas na mesma posição.</span>','red')
				return redirect(url_for('docs.document', id=str(id))+"#template_sign")
			if Templates_Signatures.query.filter(Templates_Signatures.signature.has(Signature.id==assinante.signature.first().id), Templates_Signatures.template==template).first() is not None:
				flash('<span>Você não pode adicionar a mesma assinatura em duas posições diferentes.</span>','red')
				return redirect(url_for('docs.document', id=str(id))+"#template_sign")
			if assinante.signature.first() is None:
				flash('<span>O colaborador não possui uma assinatura cadastrada.</span>','red')
				return redirect(url_for('docs.document', id=str(id))+"#template_sign")
			template_sign=Templates_Signatures(color_sign)
			template_sign.signature=assinante.signature.first()
			template_sign.template=template
			template_sign.request_date=datetime.datetime.now()
			if assinante==logged:
				template_sign.authorization_date=datetime.datetime.now()
				template_sign.authorized=1
			else:
				template_sign.authorized=0
			send_mail=0;
			for document in template.documents:
				temp_sign_toadd=Documents_Signatures()
				temp_sign_toadd.signature=assinante.signature.first()
				temp_sign_toadd.document=document
				temp_sign_toadd.request_date=datetime.datetime.now()
				if assinante==logged:
					temp_sign_toadd.authorized=1
					temp_sign_toadd.authorization_date=datetime.datetime.now()
				else:
					temp_sign_toadd.authorized=0
					temp_sign_toadd.document.available=0
					send_mail=1;
				db.session.add(temp_sign_toadd)
			db.session.commit()
			if send_mail:
				email_content("add_sign",assinante,template)
			flash('<span>Assinatura adicionada com sucesso!</span>','green')
			return redirect(url_for('docs.document', id=str(id))+"#template_sign")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/editar_assinatura/<sid>/<tid>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def edit_sign(sid=None, tid=None):
	logged=current_user
	if sid and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			color_sign=request.form['color_sign'+str(sid)]
			sign_order=Templates_Signatures.query.filter_by(signature_order=color_sign, template_id=tid).first()
			if sign_order is not None and sign_order.signature_id!= sid:
				flash('<span>Você não pode adicionar duas assinaturas na mesma posição.</span>','red')
				return redirect(url_for('docs.document', id=str(tid))+"#template_sign")
			else:
				signature=Templates_Signatures.query.filter_by(template_id=tid, signature_id=sid).first()
				if signature:
					signature.signature_order=color_sign
					db.session.commit()
					flash('<span>Edição de assinatura efetuada com sucesso!</span>','green')
					return redirect(url_for('docs.document', id=str(tid))+"#template_sign")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/excluir_assinatura/<sid>/<tid>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def delete_sign(sid=None, tid=None):
	logged=current_user
	if sid and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			Templates_Signatures.query.filter_by(signature_id=sid, template_id=tid).delete()
			Documents_Signatures.query.filter(Documents_Signatures.document.has(Document.template_id==tid),Documents_Signatures.signature_id==sid).delete(synchronize_session=False)
			db.session.commit()
			flash('<span>Assinatura excluída com sucesso!</span>','green')
			return redirect(url_for('docs.document', id=tid)+"#template_sign")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/publicar_documentos/<id>',methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def unlock_documents(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			ret=unlock_document_list(template.documents,db.session)
			if ret>1:
				flash("<span>Todos os documentos foram disponibilizados com sucesso!</span>", "green")
				return redirect(url_for('docs.document', id=str(id))+"#template_documents")
			else:
				if ret==1:
					flash("<span>Alguns documentos foram disponibilizados com sucesso, outros ainda precisam de autorização para assinatura.</span>", "orange")
					return redirect(url_for('docs.document', id=str(id))+"#template_documents")
				else:
					flash("<span>Os documentos ainda precisam de autorização para assinatura.</span>", "red")
					return redirect(url_for('docs.document', id=str(id))+"#template_documents")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/bloquear_documento/<did>/<tid>',methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def block_single_document(did=None, tid=None):
	logged=current_user
	if did and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			document=Document.query.filter_by(id=did).first()
			document.available=False
			db.session.commit()
			flash("<span>Documento bloqueado com sucesso!</span>", "green")
			return redirect(url_for('docs.document', id=str(tid))+"#template_documents")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/desbloquear_documento/<did>/<tid>',methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def unlock_single_document(did=None, tid=None):
	logged=current_user
	if did and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			document=Document.query.filter_by(id=did).first()
			ret=unlock_document_list([document], db.session)
			if ret == 0:
				flash("<span>As assinaturas para este documento estão com autorização pendente.</span>", "red")
				return redirect(url_for('docs.document', id=str(tid))+"#template_documents")
			else:
				flash("<span>Documento desbloqueado com sucesso!</span>", "green")
				return redirect(url_for('docs.document', id=str(tid))+"#template_documents")
	return redirect(url_for('admin.login'))


# Tabela Completa - document_full_table.html

@docs.route('/disponibilizar_documentos/tabela_completa/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def full_table(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			output=getNotifications(logged)
			fields=Field.query.filter_by(template_id=template.id)
			documents=Document.query.filter_by(template_id=template.id)
			j=0;
			r=[];
			for field in fields:
				i=0;
				for document in documents:
					if j==0:
						r.append([])
					value=Value.query.filter_by(document_id=document.id, field_id=field.id).first()
					r[i].append(value)
					i=i+1;
				j=1;
			maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
			return verifyMaintenance(logged, 'docs',render_template('document_full_table.html', template=template, user=logged, template_id=template.id, event_id=template.event.id, notifications=output, table=r, maintenance=maintenance))
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/tabela_completa/adicionar_participantes/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def full_table_upload_participants(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			array=request.get_array(field_name='file',encoding='latin1',library='pyexcel-xlsxr',auto_detect_float=False,auto_detect_int=False)
			sbr_table=request.form['sbr_table']
			check=checkExcelFile(array);
			if check==1:
				savevalues(array,template,logged, sbr_table)
				flash('<span>Participantes adicionados com sucesso!</span>','green')
			else:
				flash('<span>'+check+' Verifique o <a class="toast_link" href='+url_for('docs.tutorial')+'>tutorial</a>.</span>','red')
			return redirect(url_for('docs.full_table', id=str(id)))
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/tabela_completa/editar_participante/<vid>/<tid>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def full_table_edit(vid=None, tid=None):
	logged=current_user
	if vid and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			new_value=request.form['new_value_'+vid]
			value=Value.query.filter_by(id=vid).first()
			if value.value != new_value:
				value.value=new_value
				db.session.commit()
				flash('<span>Campo atualizado com sucesso!</span>','green')
			return redirect(url_for('docs.full_table', id=str(tid)))
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/tabela_completa/excluir_participante/<did>/<tid>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def full_table_delete_participant(did=None, tid=None):
	logged=current_user
	if did and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			Value.query.filter_by(document_id=int(did)).delete()
			document=Document.query.filter_by(id=int(did)).first()
			Documents_Signatures.query.filter_by(document_id=int(did)).delete()
			db.session.delete(document)
			db.session.commit()
			flash('<span>Participante excluído com sucesso!</span>','green')
			return redirect(url_for('docs.full_table', id=str(tid)))
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/tabela_completa/excluir_todos_participantes/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def delete_all_participants(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			Documents_Signatures.query.filter(Documents_Signatures.document.has(Document.template_id==id)).delete(synchronize_session=False)
			for document in template.documents:
				db.session.delete(document)
			Value.query.filter(Value.field.has(Field.template_id==id)).delete(synchronize_session=False)
			Field.query.filter_by(template_id=id).delete()
			db.session.commit()
			flash('<span>Todos os participantes foram excluídos com sucesso!</span>','green')
			return redirect(url_for('docs.document', id=str(id))+"#template_documents")
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/tabela_completa/bloquear_documento/<did>/<tid>',methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def full_table_block_single_document(did=None, tid=None):
	logged=current_user
	if did and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			document=Document.query.filter_by(id=did).first()
			document.available=False
			db.session.commit()
			flash("<span>Documento bloqueado com sucesso!</span>", "green")
			return redirect(url_for('docs.full_table', id=str(tid)))
	return redirect(url_for('admin.login'))


@docs.route('/disponibilizar_documentos/tabela_completa/desbloquear_documento/<did>/<tid>',methods = ['GET', 'POST'])
@login_required
@requires_roles(2250)
def full_table_unlock_single_document(did=None, tid=None):
	logged=current_user
	if did and tid:
		template=Template.query.filter_by(id=tid).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			document=Document.query.filter_by(id=did).first()
			ret=unlock_document_list([document], db.session)
			if ret == 0:
				flash("<span>As assinaturas para este documento estão com autorização pendente.</span>", "red")
			else:
				flash("<span>Documento desbloqueado com sucesso!</span>", "green")
			return redirect(url_for('docs.full_table', id=str(tid)))
	return redirect(url_for('admin.login'))


@docs.route("/disponibilizar_documentos/tabela_completa/exportar_tabela/<id>", methods=['GET'])
@login_required
@requires_roles(2250)
def download_file(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if template and (logged in event_administrators):
			return export_xlsx(template);
	return redirect(url_for('admin.login'))


# Download de TODOS os documentos (.zip)

@docs.route('/downloadzip/<id>', methods=['GET'])
@login_required
@requires_roles(2250)
def downloadzip(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		if template is None:
			return redirect(url_for('docs.document', id=str(id))+"#template_documents")
		event=template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		if event and (logged in event_administrators):
			return filldocuments(template,logged)
	return redirect(url_for('admin.login'))


# LISTA DE DOCUMENTOS - documents_list.html

@docs.route('/documentos/<id>', methods = ['GET', 'POST'])
@login_required
def documents(id=None):
	logged=current_user
	if id:
		documents=Document.query.filter(Document.template.has(Template.event_id==id), Document.user==logged)
		usersign=logged.signature.first()
		notifications=Documents_Signatures.query.filter_by(signature=usersign,authorized=0)
		output=getNotifications(logged)
		maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'docs',render_template('documents_list.html',documents=documents, user=logged, event_idd=id,notifications=output,maintenance=maintenance))


# PDF

@docs.route('/certificado/<code>', methods=['GET'])
def certificate(code=None):
	if code:
		logged=current_user
		document=Document.query.filter_by(code=code).first()
		if document is None:
			return redirect("/")
	return filldocument(document,logged,'inline')


@docs.route('/validar_documento', methods = ['GET', 'POST'])
def validate_document():
	if request.method == 'POST':
		codeDoc=request.form['docCode']
		document=Document.query.filter_by(code=codeDoc).first()
		event=Event.query.filter_by(id=request.args.get('event')).first()
		template=Template.query.filter_by(id=request.args.get('template')).first()
		if document is None or not document.available:
			flash('<span>Documento não registrado!</span>','red')
		else:
			return render_template('found_document.html', document=document, template=template, event=event)
	return redirect(url_for('admin.login'))


@docs.route('/teste_certificado/<code>', methods=['GET', 'POST'])
@login_required
@requires_roles(2500)
def certificate_test(code=None):
	logged=current_user
	if code:
		document=Document.query.filter_by(code=code).first()
		if document is None:
			return redirect("/")
		event=document.template.event
		event_administrators = [event_adm.user for event_adm in event.administrators]
		signedby = [relationship.signature.user for relationship in document.template.signatures]
		if (event and logged in event_administrators) or logged in signedby:
			return filldocumenttest(document,logged,'attachment')
	return redirect(url_for('admin.login'))


@docs.route('/download_certificado/<code>', methods=['GET', 'POST'])
def downloadCertificate(code=None):
	logged=current_user
	if code:
		if request.method == 'GET':
			document=Document.query.filter_by(code=code).first()
			if document is None:
				return redirect("/")
			return filldocument(document,logged,'attachment')
	return redirect(url_for('admin.login'))


# HISTÓRICO DE ASSINATURAS - signatureshistory.html

@docs.route('/assinaturas',methods = ['GET', 'POST'])
@login_required
@requires_roles(2500)
def signatureshistory():
	logged=current_user
	usersign=logged.signature.first()
	signatures=Templates_Signatures.query.filter_by(signature=usersign)
	count=signatures.count()
	output=getNotifications(logged)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'docs',render_template('signatureshistory.html', user=logged, notifications=output, signatures=signatures,signcount=count,maintenance=maintenance,gmt_timezone=GMT_TIMEZONE, timezone=TIMEZONE))


# CONFIRMAR ASSINATURA EM DOCUMENTO - signconfirmation.html

@docs.route('/confirmacao_de_assinatura/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2500)
def signconfirmation(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		usersign=logged.signature.first()
		tosignTemplate=Templates_Signatures.query.filter_by(template=template,signature=usersign).first()
		tosignDocuments=Documents_Signatures.query.filter_by(signature=usersign,authorized=0)
		documents= [tosignDocument.document for tosignDocument in tosignDocuments]
		output=getNotifications(logged)
		fields=Field.query.filter_by(template_id=template.id)
		j=0;
		r=[];
		for field in fields:
			if field is not None:
				i=0;
				for document in template.documents:
					if j==0:
						r.append([])
					value=Value.query.filter_by(document_id=document.id, field_id=field.id).first()
					r[i].append(value)
					i=i+1;
				j=1;
		maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
		return verifyMaintenance(logged, 'docs',render_template('signconfirmation.html', documents=documents, user=logged, notifications=output, template=template, tosignTemplate=tosignTemplate, maintenance=maintenance, table=r, gmt_timezone=GMT_TIMEZONE, timezone=TIMEZONE))
	return redirect(url_for('admin.login'))


@docs.route('/confirmacao_de_assinatura/confirmar/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2500)
def signconfirmation_form(id=None):
	logged=current_user
	if id:
		template=Template.query.filter_by(id=id).first()
		usersign=logged.signature.first()
		tosignDocuments=Documents_Signatures.query.join(Documents_Signatures.document).filter(Document.template==template,Documents_Signatures.signature==usersign,Documents_Signatures.authorized==0)
		tosignTemplate=Templates_Signatures.query.filter_by(template=template,signature=usersign).first()
		for tosignDocument in tosignDocuments:
			tosignDocument.authorization_date=datetime.datetime.now()
			tosignDocument.authorized=1
			log=Log(logged,"Sign",tosignDocument.document)
			db.session.add(log)
		tosignTemplate.authorized=1
		tosignTemplate.authorization_date=datetime.datetime.now()
		for administrator in tosignTemplate.template.event.administrators:
			if logged != administrator.user:
				notification=Notification(administrator.user,1,tosignTemplate.template.name+";"+logged.name)
				db.session.add(notification)
				email_content("signconfirmation",administrator.user,tosignTemplate.template,logged)
		db.session.commit()
		flash('<span>Assinatura confirmada com sucesso!</span>','green')
		return redirect(url_for('docs.signconfirmation', id=str(id)))
	return redirect(url_for('admin.login'))


# DASHBOARD - dashboard.html

@docs.route('/dashboard',methods = ['GET', 'POST'])
@login_required
@requires_roles(1000)
def dashboard():
	logged=current_user
	output=getNotifications(logged)
	template=Template.query.filter_by(id=request.args.get('template')).first()
	Readperday=db.session.query(func.count(Log.action).label('acessos'), func.date_trunc('day',Log.date).label("day")).filter(Log.action=='Read').group_by(func.date_trunc('day',Log.date)).order_by(func.date_trunc('day',Log.date))
	AveragePDFTimePerDay=db.session.query(func.avg(TimerLog.time).label('media'), func.date_trunc('day',TimerLog.date).label("day")).filter(TimerLog.operation==1).group_by(func.date_trunc('day',TimerLog.date)).order_by(func.date_trunc('day',TimerLog.date))
	AverageZIPTimePerDay=db.session.query(func.avg(TimerLog.time).label('media'), func.date_trunc('day',TimerLog.date).label("day")).filter(TimerLog.operation==2).group_by(func.date_trunc('day',TimerLog.date)).order_by(func.date_trunc('day',TimerLog.date))
	AverageBackupTimePerDay=db.session.query(func.avg(TimerLog.time).label('media'), func.date_trunc('day',TimerLog.date).label("day")).filter(TimerLog.operation==3).group_by(func.date_trunc('day',TimerLog.date)).order_by(func.date_trunc('day',TimerLog.date))
	AverageRestoreTimePerDay=db.session.query(func.avg(TimerLog.time).label('media'), func.date_trunc('day',TimerLog.date).label("day")).filter(TimerLog.operation==4).group_by(func.date_trunc('day',TimerLog.date)).order_by(func.date_trunc('day',TimerLog.date))
	DocumentsPublished=Document.query.filter_by(available=True)
	LogsDocumentsViewedByOwner=Log.query.join(Log.document).filter(Log.document.has(Document.user_id==Log.user_id), Log.action=="Read")
	DocumentsViewedByOwner=set()
	for row in LogsDocumentsViewedByOwner:
		DocumentsViewedByOwner.add(row.document)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'docs',render_template('dashboard.html', notifications=output, template=template, user=logged, Readperday=Readperday, AveragePDFTimePerDay=AveragePDFTimePerDay, AverageZIPTimePerDay=AverageZIPTimePerDay, AverageBackupTimePerDay=AverageBackupTimePerDay,AverageRestoreTimePerDay=AverageRestoreTimePerDay, DocumentsPublished=DocumentsPublished, DocumentsViewedByOwner=DocumentsViewedByOwner,maintenance=maintenance))


# NOTIFICAÇÕES - Remover Notificação

@docs.route('/remover_notificacao/<id>',methods = ['GET'])
@login_required
def dismiss_notification(id=None):
	previous=request.args.get('previous')
	logged=current_user
	if logged:
		notification=Notification.query.filter_by(id=id).first();
		notification.viewed=True;
		db.session.commit()
	return redirect(previous)
	return redirect(url_for('admin.login'))

@docs.route('/offline',methods = ['GET'])
def offlineresponse():
	return render_template('offline.html', textError='Não há conexão com a internet!')
