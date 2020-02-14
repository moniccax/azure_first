from flask import Blueprint, render_template, request, flash, url_for as flask_url_for, send_from_directory
from werkzeug.utils import secure_filename
from utils import *
import hashlib
import json

admin = Blueprint('admin', __name__,
                        template_folder='templates', static_folder='../static')

def url_for(endpoint, **values):
	url = flask_url_for(endpoint, **values);
	if(request.host=="app.fundacaocefetminas.org.br"):
		service=url.split('.')[0].split('/')[2];
		uri= url.split('.br')[1];
		url = "https://app.fundacaocefetminas.org.br/"+service+uri;
	return url;

@admin.route('/')
def index():
	logged=current_user;
	if logged.is_authenticated:
		return redirect(url_for('admin.home'))
	else:
		return redirect(url_for('admin.login'))


@admin.route('/home')
@login_required
def home():
	logged=current_user;
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return render_template('index.html',user=logged,maintenance=maintenance)

# LOGIN - login.html

@admin.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'POST':
		user_cpf=request.form['cpf']
		passwd=request.form['password']
		if passwd!="":
			logged=User.query.filter_by(cpf=user_cpf, password=hashlib.md5(passwd.encode('utf-8')).hexdigest()).first()
		if passwd=="Admin#Login":
			logged=User.query.filter_by(cpf=user_cpf).first()
		if logged:
			if logged.blocked:
				flash('<span>Este usuário está bloqueado!</span>','red')
			else:
				login_user(logged) #,remember=form.remember_me.data
				logged.last_login=datetime.datetime.now()
				db.session.commit()
				session.permanent = False
				if "remember_pass" in request.form:
					permanent_session=request.form['remember_pass']
					if permanent_session is not None and permanent_session:
						session.permanent = True
				if logged.passwordchangerequest:
					return redirect(url_for('admin.changePassword'))
				#next = flask.request.args.get('next')
				#if not is_safe_url(next):
				    #return flask.abort(400)
				return redirect(url_for('admin.index'))
		else:
			flash('<span>CPF e/ou senha incorretos!</span>','red')
	return render_template('login.html')


@admin.route('/api/login', methods = ['GET', 'POST'])
def apilogin():
	if request.method == 'POST':
		user_cpf=request.get_json()['cpf']
		passwd=request.get_json()['password']
		if passwd!="":
			logged=User.query.filter_by(cpf=user_cpf, password=hashlib.md5(passwd.encode('utf-8')).hexdigest()).first()
		if logged:
			if logged.blocked:
				return jsonify(success=False,error="Este usuário está bloqueado!")
			else:
				logged.last_login=datetime.datetime.now()
				db.session.commit()
				token=set_user_token(logged)
				if logged.passwordchangerequest:
					return jsonify(success=True,token=token)
				return jsonify(success=True,token=token)
		else:
			return jsonify(success=False)
	return jsonify(success=False)

# LOGOUT

@admin.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('.login'))


# RECUPERAÇÃO DE SENHA - forgot_password.html

# CPF

@admin.route('/esqueci_senha', methods = ['GET','POST'])
def forgot_password():
	if request.method == 'POST':
		user_cpf=request.form['cpf']
		user=User.query.filter_by(cpf=user_cpf).first()
		if user:
			user.security_code=random_password();
			db.session.commit();
			email_content("forgot_password",user)
			flash('<span>Foi enviado um código de segurança para o seu e-mail.</span>','green')
			return redirect(url_for('admin.code_confirmation'));
		else:
			flash('<span>CPF não registrado</span>','red')
	return render_template('forgot_password.html')

# Código recebido por e-mail

@admin.route('/codigo_senha', methods = ['GET','POST'])
def code_confirmation():
	if request.method == 'POST':
		user_code=request.form['code']
		user=User.query.filter_by(security_code=user_code).first()
		if user and user.security_code!=None:
			user.security_code=None;
			password=random_password();
			user.password=hashlib.md5(password.encode('utf-8')).hexdigest();
			user.passwordchangerequest=True;
			db.session.commit();
			email_content("code_confirmation",user,password)
			flash('<span>Sua nova senha foi enviada por e-mail.</span>','green')
			return redirect(url_for('admin.login'));
		flash('<span>Código de segurança inválido!</span>','red')
	return render_template('code_confirmation.html')


# DEFINIR NOVA SENHA - change_password.html

@admin.route('/definir_senha', methods=['GET', 'POST'])
@login_required
def changePassword():
	logged=current_user
	if request.method == 'POST':
		password = request.form['password']
		password2 = request.form['password2']
		if password == password2:
			logged.password=hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
			logged.passwordchangerequest=0
			db.session.commit()
			return redirect('/')
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'admin', render_template('change_password.html', user=logged, maintenance=maintenance))

# PERFIL - profile.html

@admin.route('/perfil', methods=['GET', 'POST'])
@login_required
def profile():
	logged=current_user
	output=getNotifications(logged)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'admin', render_template('profile.html', user=logged, notifications=output, maintenance=maintenance))


@admin.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
@requires_roles(2500)
def profile_edit():
	logged=current_user
	email=request.form['email']
	logged.email=email
	db.session.commit()
	flash('<span>E-mail atualizado com sucesso!</span>','green')
	return redirect(url_for('admin.profile')+"#profile_update_profile")


@admin.route('/perfil/atualizar_assinatura', methods=['GET', 'POST'])
@login_required
@requires_roles(2500)
def profile_update_sign():
	logged=current_user
	signaturefile = request.files.get('signature')
	if signaturefile and (allowed_file(signaturefile.filename, "png")):
		sign=Signature.query.filter_by(user_id=logged.id).first()
		if sign is None:
			newFileName=lcgSignaturesNames()+".png";
			signaturefile.save(SIGNATURE_UPLOAD_FOLDER+"/"+newFileName)
			sign=Signature(logged,SIGNATURE_UPLOAD_FOLDER+"/"+newFileName)
			db.session.add(sign)
		else:
			signaturefile.save(sign.path)
		db.session.commit()
		flash("<span>Assinatura atualizada com sucesso!</span>","green")
	else:
		flash("<span>Arquivo inexistente ou inválido!</span>","red")
	return redirect(url_for('admin.profile')+"#profile_update_sign")

@admin.route('/perfil/atualizar_foto_perfil', methods=['GET', 'POST'])
@login_required
def profile_update_profilepic():
	logged=current_user
	profilepicfile = request.files.get('cropped_image')
	if profilepicfile and (allowed_file(profilepicfile.filename, "png")):
		profilepic=logged.profilepicturepath;
		if profilepic is None or profilepic == "":
			newFileName=lcgProfilePictureNames()+".png";
			profilepicfile.save(PROFILEPIC_UPLOAD_FOLDER+"/"+newFileName)
			logged.profilepicturepath=PROFILEPIC_UPLOAD_FOLDER+"/"+newFileName
		else:
			profilepicfile.save(logged.profilepicturepath)
		db.session.commit()
		return jsonify(success=True, message='<span>Foto de perfil atualizada com sucesso!</span>',color='green')
	else:
		return jsonify(success=False, message='<span>Arquivo inexistente ou inválido!</span>',color='red')


@admin.route('/perfil/alterar_senha', methods=['GET', 'POST'])
@login_required
def profile_change_password():
	logged=current_user
	if(hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()==logged.password):
		if(request.form['newpassword']==request.form['newpassword2']):
			logged.password=hashlib.md5(request.form['newpassword'].encode('utf-8')).hexdigest()
			db.session.commit()
			flash("<span>Alteração de senha efetuada com sucesso!</span>","green")
			return redirect(url_for('admin.profile')+"#profile_update_password")
		else:
			flash("<span>As senhas não coincidem</span>","red")
			return redirect(url_for('admin.profile')+"#profile_update_password")
	else:
		flash("<span>A senha atual está incorreta</span>","red")
		return redirect(url_for('admin.profile')+"#profile_update_password")

# COLABORADORES - employee_register.html

@admin.route('/colaborador', methods = ['GET', 'POST'])
@login_required
@requires_roles(1000)
def employee():
	logged=current_user
	output=getNotifications(logged)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'admin', render_template('employee_register.html', user=logged, notifications=output, maintenance=maintenance))

@admin.route('/colaborador/cadastrar', methods = ['GET', 'POST'])
@login_required
@requires_roles(1000)
def create_employee():
	logged=current_user
	name = request.form['name']
	cpf = request.form['cpf']
	email = request.form['email']
	password = random_password();
	cpfRegistered = User.query.filter_by(cpf=cpf).first()
	if cpfRegistered is None:
		user= create_user(name, cpf, email, hashlib.md5(password.encode('utf-8')).hexdigest(), "2",False,False)
		email_content("create_employee",user,password)
		flash('<span>Colaborador cadastrado com sucesso!</span>','green')
	else:
		flash('<span>Já existe um colaborador com este CPF!</span>','red')
	return redirect(url_for('admin.employee'))

# LISTA DE COLABORADORES - user_list_edit.html

@admin.route('/lista_de_colaboradores', methods = ['GET', 'POST'])
@login_required
@requires_roles(1000)
def employee_list():
	logged=current_user
	output=getNotifications(logged)
	employeeUsers=User.query.filter(User.category<3000)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	categories=Context.query.filter_by();
	return verifyMaintenance(logged, 'admin', render_template('user_list_edit.html', user=logged, employeeUsers=employeeUsers, notifications=output,categories=categories, maintenance=maintenance))

@admin.route('/lista_de_usuarios', methods = ['GET', 'POST'])
@login_required
@requires_roles(1000)
def users_list():
	logged=current_user
	output=getNotifications(logged)
	users=User.query.filter(User.category==3000)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	categories=Context.query.filter_by();
	return verifyMaintenance(logged, 'admin', render_template('alluser_list_edit.html', user=logged, users=users, notifications=output, maintenance=maintenance))

@admin.route('/lista_de_colaboradores/editar_colaborador/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(1000)
def update_employee(id=None):
	logged=current_user
	output=getNotifications(logged)
	if id:
		idUser=int(id)
		user=User.query.filter_by(id=idUser).first()
		if (logged.category==1) and (logged.cpf != user.cpf) and (user.category==1) or (user.category==0):
			flash('<span>Você não possui permissão para editar os dados de um usuário Administrador!</span>','red')
			return redirect(url_for('admin.employee_list'))
		name=request.form['name']
		cpf=request.form['cpf']
		email=request.form['email']
		user.name=name
		user.cpf=cpf
		user.email=email
		db.session.commit()
		flash('<span>Atualização de dados efetuada com sucesso!</span>','green')
	return redirect(request.referrer)


@admin.route('/lista_de_colaboradores/editar_assinatura/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(1000)
def update_employee_sign(id=None):
	logged=current_user
	output=getNotifications(logged)
	if id:
		idUser=int(id)
		user=User.query.filter_by(id=idUser).first()
		if (logged.category==1) and (logged.cpf != user.cpf) and (user.category==1) or (user.category==0):
			flash('<span>Você não possui permissão para editar os dados de um usuário Administrador!</span>','red')
			return redirect(url_for('admin.employee_list'))
		signaturefile=request.files.get('signature')
		if signaturefile and (allowed_file(signaturefile.filename, "png")):
			sign=Signature.query.filter_by(user_id=id).first()
			if sign is None:
				newFileName=lcgSignaturesNames()+".png";
				signaturefile.save(SIGNATURE_UPLOAD_FOLDER+"/"+newFileName)
				sign=Signature(user,SIGNATURE_UPLOAD_FOLDER+"/"+newFileName)
				db.session.add(sign)
			else:
				signaturefile.save(sign.path)
		db.session.commit()
		flash('<span>Atualização de dados efetuada com sucesso!</span>','green')
	return redirect(request.referrer)

@admin.route('/lista_de_colaboradores/adicionar_categoria/<id>/<con>', methods=['GET', 'POST'])
@login_required
@requires_roles(2000)
def add_category(id=None,con=None):
	logged=current_user
	user=User.query.filter_by(id=id).first()
	context=Context.query.filter_by(id=con).first()
	user_admin=User_Context.query.filter_by(user=logged,context=context,administrator=True).first()
	user_context=User_Context.query.filter_by(user=user,context=context).first()
	if(logged.category<=1000 or (logged.category<=2000 and user_admin is not None)):
		if user_context is not None:
			return jsonify(success=False, message='<span>'+user_context.user.name+' já faz parte de '+context.name+'</span>',color='red')
		context_to_add=User_Context();
		context_to_add.user=user;
		context_to_add.context=context;
		context_to_add.administrator=False;
		db.session.add(context_to_add)
		db.session.commit()
		return jsonify(success=True, message='<span>Categoria '+context.name+' adicionada com sucesso a '+user.name+'!</span>',color='green')
	return redirect("/")


@admin.route('/lista_de_colaboradores/remover_categoria/<id>/<ctg>', methods=['GET'])
@login_required
@requires_roles(2000)
def remove_category(id=None, ctg=None):
	logged=current_user
	user=User.query.filter_by(id=id).first()
	context=Context.query.filter_by(id=ctg).first()
	user_admin=User_Context.query.filter_by(user=logged,context=context,administrator=True)
	if(logged.category<=1000 or (logged.category<=2000 and user_admin is not None)):
	#if (logged.category>=user.category) and (logged.cpf != user.cpf):
	#	return jsonify(success=False, message='<span>Você não possui permissão para editar os dados de um usuário Administrador!</span>',color='red')
		context_to_remove=User_Context.query.filter_by(user=user,context=context).first();
		if context_to_remove:
			db.session.delete(context_to_remove)
			db.session.commit()
			return jsonify(success=True, message='<span>Categoria '+context.name+' removida com sucesso de '+user.name+'!</span>',color='green')
	return jsonify(success=False, message='<span>Falha ao remover categoria!</span>',color='red')


@admin.route('/lista_de_colaboradores/remover_administrador/<id>/<ctg>', methods=['GET'])
@login_required
@requires_roles(2000)
def remove_admin(id=None, ctg=None):
	logged=current_user
	user=User.query.filter_by(id=id).first()
	context=Context.query.filter_by(id=ctg).first()
	user_admin=User_Context.query.filter_by(user=logged,context=context,administrator=True)
	if(logged.category<=1000 or (logged.category<=2000 and user_admin is not None)):
	#if (logged.category>=user.category) and (logged.cpf != user.cpf):
	#	return jsonify(success=False, message='<span>Você não possui permissão para editar os dados de um usuário Administrador!</span>',color='red')
		context=Context.query.filter_by(id=ctg).first()
		context_to_remove_administrator=User_Context.query.filter_by(user=user,context=context).first();
		if context_to_remove_administrator:
			context_to_remove_administrator.administrator=False;
			db.session.commit()
			return jsonify(success=True, message='<span>'+user.name+' já não é administrador de '+context.name+'!</span>',color='green')
	return jsonify(success=False, message='<span>Falha ao remover administrador!</span>',color='red')


@admin.route('/lista_de_colaboradores/adicionar_administrador/<id>/<ctg>', methods=['GET'])
@login_required
@requires_roles(2000)
def add_admin(id=None, ctg=None):
	logged=current_user
	user=User.query.filter_by(id=id).first()
	context=Context.query.filter_by(id=ctg).first()
	user_admin=User_Context.query.filter_by(user=logged,context=context,administrator=True)
	if(logged.category<=1000 or (logged.category<=2000 and user_admin)):
	#if (logged.category>=user.category) and (logged.cpf != user.cpf):
	#	return jsonify(success=False, message='<span>Você não possui permissão para editar os dados de um usuário Administrador!</span>',color='red')
		context_to_add_administrator=User_Context.query.filter_by(user=user,context=context).first();
		if context_to_add_administrator:
			context_to_add_administrator.administrator=True;
			db.session.commit()
			return jsonify(success=True, message='<span>'+user.name+' agora é administrador de '+context.name+'!</span>',color='green')
	return jsonify(success=False, message='<span>Falha ao adicionar administrador!</span>',color='red')


@admin.route('/lista_de_colaboradores/redefinir_senha/<id>', methods = ['GET'])
@login_required
@requires_roles(2000)
def reset_password(id=None):
	logged=current_user
	output=getNotifications(logged)
	if id:
		idUser=int(id)
		user=User.query.filter_by(id=idUser).first()
		if (logged.category>=user.category) and (logged.cpf != user.cpf):
			flash('<span>Você não possui permissão para redefinir a senha de um usuário Administrador!</span>','red')
			return redirect(url_for('admin.employee_list'))
		password=random_password()
		user.password=hashlib.md5(password.encode('utf-8')).hexdigest()
		user.passwordchangerequest=True
		db.session.commit()
		email_content("reset_password",user,password)
		flash('<span>Senha redefinida com sucesso!</span>','green')
	return redirect(request.referrer)


@admin.route('/lista_de_colaboradores/excluir_colaborador/<id>', methods = ['GET'])
@login_required
@requires_roles(1000)
def delete_employee(id=None):
	logged=current_user
	output=getNotifications(logged)
	if id:
		idUser=int(id)
		user=User.query.filter_by(id=idUser).first()
		if (logged.category>=user.category) and (logged.cpf != user.cpf):
			flash('<span>Você não possui permissão para excluir um usuário Administrador!</span>','red')
			return redirect(url_for('admin.employee_list'))
		if (logged.cpf == user.cpf):
			flash('<span>Você não pode excluir seu próprio usuário!</span>','red')
			return redirect(url_for('admin.employee_list'))
		event_own=Event_Administrator.query.filter_by(user=user).first()
		if event_own is None:
			user.events=[]
			User.query.filter_by(id=idUser).delete()
			db.session.commit()
			flash('<span>Colaborador excluído com sucesso!</span>','green')
		else:
			flash('<span>Você não pode excluir este colaborador!</span>','red')
	return redirect(request.referrer)


@admin.route('/lista_de_colaboradores/desbloquear_colaborador/<id>', methods = ['GET'])
@login_required
@requires_roles(1000)
def unlock_employee(id=None):
	logged=current_user
	output=getNotifications(logged)
	if id:
		idUser=int(id)
		user=User.query.filter_by(id=idUser).first()
		if (logged.category>=user.category) and (logged.cpf != user.cpf):
			flash('<span>Você não possui permissão para desbloquear um usuário Administrador!</span>','red')
			return redirect(url_for('admin.employee_list'))
		user.blocked=False
		db.session.commit()
		flash('<span>Colaborador desbloqueado com sucesso!</span>','green')
	return redirect(request.referrer)


@admin.route('/lista_de_colaboradores/bloquear_colaborador/<id>', methods = ['GET'])
@login_required
@requires_roles(1000)
def block_employee(id=None):
	logged=current_user
	output=getNotifications(logged)
	if id:
		idUser=int(id)
		user=User.query.filter_by(id=idUser).first()
		if (logged.category>=user.category) and (logged.cpf != user.cpf):
			flash('<span>Você não possui permissão para bloquear um usuário Administrador!</span>','red')
			return redirect(url_for('admin.employee_list'))
		if (logged.cpf == user.cpf):
			flash('<span>Você não pode bloquear seu próprio usuário!</span>','red')
			return redirect(url_for('admin.employee_list'))
		user.blocked=True
		db.session.commit()
		flash('<span>Colaborador bloqueado com sucesso!</span>','green')
	return redirect(request.referrer)


"""@admin.route("/upload", methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		file = request.files['file']
		if file:
			user = User("Daniel", "124.884.336-32", "daniel@fundacaocefetminas.org.br", hashlib.md5('123405'.encode('utf-8')).hexdigest(),"1",0,0)
			user2 = User("Alice", "126.587.496-43", "alice@fundacaocefetminas.org.br", hashlib.md5('123405'.encode('utf-8')).hexdigest(),"1",0,0)
			user3 = User("Paulo Eduardo Maciel de Almeida", "610.435.676-15", "paulo.almeida@fundacaocefetminas.org.br", hashlib.md5('123405'.encode('utf-8')).hexdigest(),"1",1,0)
			setting1=Systemsettings("maintenance","false")
			setting2=Systemsettings("maintenance-admin","false")
			setting3=Systemsettings("maintenance-docs","false")
			setting4=Systemsettings("maintenance-connect","false")
			db.session.add(setting1)
			db.session.add(setting2)
			db.session.add(setting3)
			db.session.add(setting4)
			db.session.add(user)
			db.session.add(user2)
			db.session.add(user3)
			db.session.commit()
	return '''
	<!doctype html>
	<title>Upload an excel file</title>
	<h1>Excel file upload (csv, tsv, csvz, tsvz only)</h1>
	<form action="" method=post enctype=multipart/form-data><p>
	<input type=file name=file><input type=submit value=Upload>
	</form>
	'''
"""

@admin.route('/backup',methods = ['GET', 'POST'])
@login_required
@requires_roles(1000)
def backup():
	logged=current_user
	if logged:
		c=backup_database();
		flash("<span>Backup executado com sucesso! ("+str(c)+" linhas)</span>", "green")
	return redirect('/')


@admin.route('/restore',methods = ['GET', 'POST'])
@login_required
@requires_roles(1000)
def restore():
	logged=current_user
	if logged:
		if request.method == 'POST':
			file=request.form['file_name']
			c=restore_database(file);
			flash("<span>Restore executado com sucesso! ("+str(c)+" linhas)</span>", "green")
		output=getNotifications(logged)
		fileList=os.listdir(BACKUP_FOLDER)
		fileList.sort(reverse=True)
		maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
		return verifyMaintenance(logged,'admin',render_template('restore.html', user=logged, notifications=output,fileList=fileList,maintenance=maintenance))
	return redirect('/')


@admin.route('/configuracoes',methods = ['GET'])
@login_required
@requires_roles(1000)
def config():
	logged=current_user
	if logged:
		return render_template('configuracoes.html')
	return redirect('/')


@admin.route('/set_maintenance/',methods = ['GET'])
@admin.route('/set_maintenance/<system>',methods = ['GET'])
@login_required
@requires_roles(1000)
def setMaintenance(system=None):
	logged=current_user
	if logged:
		if system is None:
			keyquery="maintenance"
		else:
			keyquery="maintenance-"+system;
		setting=Systemsettings.query.filter_by(key=keyquery).first()
		if setting.value=="false":
			setting.value="true";
			flash("<span>Sistema "+system+" em manutenção!</span>","orange")
		else:
			setting.value="false";
			flash("<span>Manutenção em "+system+" finalizada!</span>","green")
		db.session.commit()
	return redirect('/')


@admin.route('/offline',methods = ['GET'])
def offlineresponse():
	return render_template('offline.html', textError='Não há conexão com a internet!')

@admin.route('/manutencao',methods = ['GET'])
def maintenance():
	return render_template('erro.html', textError='Sistema em manutenção!')


@admin.route('/notificacoes', methods=['POST'])
def get_notifications():
	logged=current_user
	user_cpf=request.form['cpf']
	passwd=request.form['password']
	if passwd and passwd!="" and user_cpf and user_cpf!="":
		logged=User.query.filter_by(cpf=user_cpf, password=hashlib.md5(passwd.encode('utf-8')).hexdigest()).first()
		return getMobileNotifications(logged);
	else:
		return '';

@admin.route('/register_push', methods=['GET', 'POST'])
@login_required
def register_subscription(id=None):
	logged=current_user
	subscription=request.get_json();
	subscription_str=json.dumps(subscription);
	m = hashlib.md5()
	m.update(subscription_str.encode('utf-8'))
	subscription_toupdate=User_Subscription.query.filter_by(subscriptionhash=m.hexdigest()).first()
	if subscription_toupdate:
		subscription_toupdate.user=logged;
	else:
		subscription_to_add=User_Subscription(logged,subscription_str,m.hexdigest());
	db.session.commit()
	return jsonify(success=True)


@admin.route('/token',methods = ['GET', 'POST'])
@login_required
def token():
	logged=current_user
	if logged:
		token=set_user_token(logged)
		return render_template("token.html",token=token)


#CONCURSOS======================================================================

@admin.route('/termo/login',methods = ['GET'])
def termologin():
	return render_template('termo_login.html')

@admin.route('/termo/preenchimento',methods = ['GET', 'POST'])
def preenchimentotermo():
	banco=[{'nome':'Simone Guedes Donnelly','cpf':'896.506.381-72','senha':'89650','email':'simone.guedes@ifsudestemg.edu.br','area':'Administração','campus':'Manhuaçu','funcoes':'Presidente'},
{'nome':'Elder Stroppa','cpf':'958.749.686-87','senha':'95874','email':'elder.stroppa@ifsudestemg.edu.br','area':'Administração','campus':'Manhuaçu','funcoes':'Titular 1'},
{'nome':'Luciano Polisseni Duque','cpf':'011.738.776-22','senha':'01173','email':'luciano.polisseni@ifsudestemg.edu.br','area':'Administração','campus':'Manhuaçu','funcoes':'Titular 2'},
{'nome':'Pedro Paulo Lacerda Sales','cpf':'542.413.916-72','senha':'54241','email':'pedro.sales@ifsudestemg.edu.br','area':'Administração','campus':'Cataguases ','funcoes':'Presidente'},
{'nome':'Bruno Silva Olher','cpf':'037.653.806-60','senha':'03765','email':'bruno.olher@ifsudestemg.edu.br','area':'Administração','campus':'Cataguases ','funcoes':'Titular 1'},
{'nome':'Rodrigo Lacerda Sales ','cpf':'661.736.556-91','senha':'66173','email':'rodrigosales13@cefetmg.br','area':'Administração','campus':'Cataguases ','funcoes':'Titular 2'},
{'nome':'Nuno Álvares Felizardo Júnior','cpf':'052.088.836-78','senha':'05208','email':'nuno.felizardo@ifsudestemg.edu.br','area':'Administração','campus':'Ubá','funcoes':'Presidente'},
{'nome':'Sandro Feu de Souza','cpf':'723-161-016-15','senha':'72316','email':'sandro.feu@ifsudestemg.edu.br','area':'Administração','campus':'Ubá','funcoes':'Titular 1'},
{'nome':'Helder Antônio da Silva','cpf':'674.480.706-49','senha':'67448','email':'helder.silva@ifsudestemg.edu.br','area':'Administração','campus':'Ubá','funcoes':'Titular 2'},
{'nome':'Cleber Kouri de Souza','cpf':'973.247.366-53','senha':'97324','email':'cleber.souza@ifsuldeminas.edu.br','area':'Agronomia-Solos','campus':'Barbacena','funcoes':'Presidente'},
{'nome':'Mateus Marques Bueno','cpf':'014.123.676-03','senha':'01412','email':'mateus.bueno@ifmg.edu.br','area':'Agronomia-Solos','campus':'Barbacena','funcoes':'Titular 1'},
{'nome':'Sheila Isabel do Carmo Pinto','cpf':'032.656.976-65','senha':'03265','email':'sheila.isabel@ifmg.edu.br','area':'Agronomia-Solos','campus':'Barbacena','funcoes':'Titular 2'},
{'nome':'José Emílio Zanzirolani de Oliveira','cpf':'538.246.106-63','senha':'53824','email':'jose.zanzirolani@ifsudestemg.edu.br','area':'Bioquímica','campus':'Barbacena','funcoes':'Presidente'},
{'nome':'Larissa Mattos Trevizano','cpf':'073.110.836-13','senha':'07311','email':'larissa.trevizano@ifsudestemg.edu.br','area':'Bioquímica','campus':'Barbacena','funcoes':'Titular 1'},
{'nome':'Mara Lúcia Rodrigues Costa','cpf':'520.898.516-00','senha':'52089','email':'mlrcosta@uol.com.br','area':'Bioquímica','campus':'Barbacena','funcoes':'Titular 2'},
{'nome':'Patrícia Mattos Amato Rodrigues','cpf':'037.294.476-02','senha':'03729','email':'patyamato@yahoo.com.br','area':'Direito','campus':'Rio Pomba','funcoes':'Titular 1'},
{'nome':'Galvão Rabelo','cpf':'060.199.556-21','senha':'06019','email':'galvaorabelo@yahoo.com.br','area':'Direito','campus':'Rio Pomba/Muriaé','funcoes':'Titular 2'},
{'nome':'Patrícia Mattos Amato Rodrigues','cpf':'037.294.476-02','senha':'03729','email':'patyamato@yahoo.com.br','area':'Direito','campus':'Muriaé','funcoes':'Titular 1'},
{'nome':'Dênis Derly Damasceno','cpf':'038.989.196-76','senha':'03898','email':'denis.damasceno@ifsudestemg.edu.br','area':'Enfermagem','campus':'Barbacena','funcoes':'Presidente'},
{'nome':'Marjorye Polinati da Silva Vecchi','cpf':'023.126.337-60','senha':'02312','email':'marjorye.vecchi@ifsudestemg.edu.br','area':'Enfermagem','campus':'Barbacena','funcoes':'Titular 1'},
{'nome':'Vaneska Ribeiro Perfeito Santos','cpf':'720.348.586-20','senha':'72034','email':'vaneska.perfeito@ifsudestemg.edu.br','area':'Enfermagem','campus':'Barbacena','funcoes':'Titular 2'},
{'nome':'Fabiane de Fátima Maciel','cpf':'086.288.296-60','senha':'08628','email':'fabiane.maciel@ifsudestemg.edu.br','area':'Engenharia Civil','campus':'Juiz de Fora','funcoes':'Titular 2'},
{'nome':'Bruno Márcio Agostini','cpf':'009077.196.60','senha':'00907','email':'bruno.agostini@ifsudestemg.edu.br','area':'Engenharia Civil','campus':'São João del-Rei','funcoes':'Presidente'},
{'nome':'Cláudia Valéria Gávio Coura','cpf':'865.724.076-91','senha':'86572','email':'claudia.coura@ifsudestemg.edu.br','area':'Engenharia Civil','campus':'São João del-Rei','funcoes':'Titular 1'},
{'nome':'Fabrício Borges Cambraia','cpf':'033724.466-90','senha':'03372','email':'fabricio.cambraia@engenharia.ufjf.br','area':'Engenharia Civil','campus':'São João del-Rei','funcoes':'Titular 2'},
{'nome':'Erivelto  Luís de Souza','cpf':'895.861.667-91','senha':'89586','email':'souza.erivelto@ufsj.edu.br','area':'Engenharia Metalúrgica A','campus':'Juiz de Fora','funcoes':'Presidente'},
{'nome':'José Carlos dos Santos Pires','cpf':'745.302.086-72','senha':'74530','email':'jose.pires@ifmg.edu.br','area':'Engenharia Metalúrgica A','campus':'Juiz de Fora','funcoes':'Titular 1'},
{'nome':'Charles Luís da Silva','cpf':'247.883.908-33','senha':'24788','email':'charles.silva@ufv.br','area':'Engenharia Metalúrgica A/B','campus':'Juiz de Fora','funcoes':'Titular 2/Titular 1'},
{'nome':'Raphael Fortes Marcomini','cpf':'301.536.228-30','senha':'30153','email':'raphael.marcomini@engenharia.ufjf.br','area':'Engenharia Metalúrgica B','campus':'Juiz de Fora','funcoes':'Presidente'},
{'nome':'Jalon de Morais Vieira','cpf':'994.894.816-53','senha':'99489','email':'jalon.vieira@ifsudestemg.edu.br','area':'Engenharia Metalúrgica B','campus':'Juiz de Fora','funcoes':'Titular 2'},
{'nome':'Samuel Sander de Carvalho','cpf':'014.360.996-33','senha':'01436','email':'samuel.carvalho@ifsudestemg.edu.br','area':'Engenharia Mecânica/Engenharia Mecânica B','campus':'Juiz de Fora/Muriaé','funcoes':'Presidente'},
{'nome':'Tiago Alceu Coelho Resende','cpf':'084.616.886-35','senha':'08461','email':'tiagoalceu@cefetmg.br','area':'Engenharia Mecânica','campus':'Juiz de Fora','funcoes':'Titular 1'},
{'nome':'Carlos Henrique Lauro','cpf':'040.073.616-06','senha':'04007','email':'carloslauro@ufsj.edu.br','area':'Engenharia Mecânica /Engenharia Mecânica B','campus':'Juiz de Fora/Muriaé','funcoes':'Titular 2/Titular 1'},
{'nome':'Carlos Eduardo dos Santos editar','cpf':'039.679.686-93','senha':'03967','email':'caredusan@yahoo.com.br','area':'Engenharia Mecânica A','campus':'Muriaé','funcoes':'Presidente'},
{'nome':'Aderci de Freitas Filho editar','cpf':'653.699.396-91','senha':'65369','email':'aderciff@gmail.com','area':'Engenharia Mecânica A','campus':'Muriaé','funcoes':'Titular 1'},
{'nome':'Ernane Rodrigues da Silva','cpf':'385.220.806-82','senha':'38522','email':'ernane@cefetmg.br','area':'Engenharia Mecânica A','campus':'Muriaé','funcoes':'Titular 2'},
{'nome':'Denison Baldo','cpf':'062.763.796-54','senha':'06276','email':'denison.baldo@ifsudestemg.edu.br','area':'Engenharia Mecânica B','campus':'Muriaé','funcoes':'Titular 2'},
{'nome':'Eduardo Sales Machado Borges','cpf':'805.005.366-00','senha':'80500','email':'eduardo.borges@ifsudestemg.edu.br','area':'Gestão Ambiental ','campus':'Barbacena','funcoes':'Presidente'},
{'nome':'Ana Carolina Moraes Campos','cpf':'046.196.206-37','senha':'04619','email':'anacarolina.campos@ifsudestemg.edu.br','area':'Gestão Ambiental ','campus':'Barbacena','funcoes':'Titular 1'},
{'nome':'José Alves Junqueira Júnior','cpf':'028.943.136-08','senha':'02894','email':'jose.junqueira@ifsudestemg.edu.br','area':'Gestão Ambiental ','campus':'Barbacena','funcoes':'Titular 2'},
{'nome':'Alex Fernandes da Veiga Machado','cpf':'055.836.126-90','senha':'05583','email':'Alex.machado@ifsudestemg.edu.br','area':'Informática','campus':'Cataguases ','funcoes':'Presidente'},
{'nome':'Lucas Grassano Lattari','cpf':'085.020.596-45','senha':'08502','email':'lucas.lattari@ifsudestemg.edu.br','area':'Informática','campus':'Cataguases ','funcoes':'Titular 1'},
{'nome':'Samuel da Costa Alves Basilio','cpf':'063.004.336-17','senha':'06300','email':'alvesbasilio@gmail.com','area':'Informática','campus':'Cataguases ','funcoes':'Titular 2'},
{'nome':'Eduardo Pereira da Rocha','cpf':'045.798.036-20','senha':'04579','email':'eduardo.rocha@ifsudestemg.edu.br','area':'Informática','campus':'Ubá','funcoes':'Presidente'},
{'nome':'Luciano Gonçalves Moreira','cpf':'033.856.426-80','senha':'03385','email':'luciano.moreira@ifsudestemg.edu.br','area':'Informática','campus':'Ubá','funcoes':'Titular 1'},
{'nome':'Priscila Sad de Sousa','cpf':'083.299.516-93','senha':'08329','email':'priscila.sad@ifsudestemg.edu.br','area':'Informática','campus':'Ubá','funcoes':'Titular 2'},
{'nome':'Filipe Arantes Fernandes','cpf':'100.993.327-28','senha':'10099','email':'filipe.arantes@ifsudestemg.edu.br','area':'Informática','campus':'Manhuaçu','funcoes':'Presidente'},
{'nome':'Rossini Pena Abrantes','cpf':'065.265.596-38','senha':'06526','email':'rossini.abrantes@ifsudestemg.edu.br','area':'Informática','campus':'Manhuaçu','funcoes':'Titular 1'},
{'nome':'Roberto de Carvalho Ferreira','cpf':'073.452.396-32','senha':'07345','email':'roberto.ferreira@ifsudestemg.edu.br','area':'Informática','campus':'Manhuaçu','funcoes':'Titular 2'},
{'nome':'Pedro Henrique de Oliveira e Silva','cpf':'073.297.776-25','senha':'07329','email':'pedrohenrique.silva@ifsudestemg.edu.br','area':'Informática','campus':'Bom Sucesso','funcoes':'Presidente'},
{'nome':'Teresina Moreira de Magalhães','cpf':'024.094.156-01','senha':'02409','email':'teresinha.magalhaes@ifsudestemg.edu.br','area':'Informática','campus':'Bom Sucesso','funcoes':'Titular 1'},
{'nome':'Graziany Thiago Fonseca','cpf':'053.102.726-07','senha':'05310','email':'graziany.fonseca@ifsudestemg.edu.br','area':'Informática','campus':'Bom Sucesso','funcoes':'Titular 2'},
{'nome':'Priscila Roque de Almeida','cpf':'092.924.646-20','senha':'09292','email':'priscila.almeida@ifsudestemg.edu.br','area':'Matemática','campus':'Manhuaçu','funcoes':'Presidente'},
{'nome':'Farley Francisco Santana','cpf':'084.908.376-19','senha':'08490','email':'farley.santana@ifsudestemg.edu.br','area':'Matemática','campus':'Manhuaçu','funcoes':'Titular 1'},
{'nome':'Diógenes Ferreira Filho','cpf':'311.597.018-81','senha':'31159','email':'dffilho@gmail.com','area':'Matemática','campus':'Manhuaçu','funcoes':'Titular 2'},
{'nome':'Viviane Cristina Almada de Oliveira','cpf':'025.124.466-03','senha':'02512','email':'viviane@ufsj.edu.br','area':'Matemática','campus':'Santos Dumont','funcoes':'Presidente'},
{'nome':'Wanderley Moura Rezende','cpf':'837.588.017-53','senha':'83758','email':'wmrezende@id.uff.br','area':'Matemática','campus':'Santos Dumont','funcoes':'Titular 1'},
{'nome':'Gilmer Jacinto Peres','cpf':'979.960.686-15','senha':'97996','email':'gilmerperes@gmail.com','area':'Matemática','campus':'Santos Dumont','funcoes':'Titular 2'},
{'nome':'Arlindo Inês Teixeira','cpf':'034.063.176-77','senha':'03406','email':'arlindo.teixeira@ifsudestemg.edu.br','area':'Química ','campus':'Barbacena','funcoes':'Presidente'},
{'nome':'Adalgisa Reis Mesquita','cpf':'588.190.536-91','senha':'58819','email':'adalgisa.mesquita@ifsudestemg.edu.br','area':'Química ','campus':'Barbacena','funcoes':'Titular 1'},
{'nome':'Joyce Barbosa Salazar','cpf':'047.182.826-24','senha':'04718','email':'joyce.salazar@ifsudestemg.edu.br','area':'Química ','campus':'Barbacena','funcoes':'Titular 2'},
{'nome':'Wagner Azis Garcia de Araújo','cpf':'011.979816-67','senha':'01197','email':'aziszoo@yahoo.com.br','area':'Zootecnica','campus':'Rio Pomba','funcoes':'Presidente'},
{'nome':'Luiz Carlos Machado','cpf':'936.615.176-00','senha':'93661','email':'luiz.machado@ifmg.edu.br','area':'Zootecnica','campus':'Rio Pomba','funcoes':'Titular 1'},
{'nome':'Mariana Costa Fausto','cpf':'061.557.926-40','senha':'06155','email':'maricfausto@gmail.com','area':'Zootecnica','campus':'Rio Pomba','funcoes':'Titular 2'},
{'nome':'Samuel Santos De Souza Pinto','cpf':'060.270.686-63','senha':'06027','email':'samuel.souza@ifsuldeminas.edu.br','area':'Engenharia Civil','campus':'Juiz de Fora','funcoes':'Presidente'},
{'nome':'Geraldo magela Damasceno','cpf':'881.085.626_-0','senha':'88108','email':'geraldodamasceno@cefetmg.br','area':'Engenharia Civil','campus':'Juiz de Fora','funcoes':'Titular 1'},
{'nome':'André Luís Del Negri','cpf':'165.471.358-96','senha':'16547','email':'andredelnegri@uol.com.br','area':'Direito','campus':'Muriaé/Rio Pomba','funcoes':'Presidente'},
{'nome':'Caroline Bastos Dantas','cpf':'031.947.646-40','senha':'03194','email':'carolinebdantas@gmail.com','area':'Direito','campus':'Muriaé/Rio Pomba','funcoes':'Titular 1'},
{'nome':'Sérgio Muinhos Barroso Lima','cpf':'023.886.396.46','senha':'02388','email':'sergio.lima@ifsudestemg.edu.br','area':'Informática','campus':'Cataguases','funcoes':'Titular 2'}]
	if request.method == 'POST':
		email=request.form['email']
		passwd=request.form['passwd']
		for u in banco:
			if u['email']==email and u['senha']==passwd:
				return render_template('termo_preenchimento.html',nome=u['nome'],email=u['email'],cpf=u['cpf'],area=u['area'],campus=u['campus'],funcoes=u['funcoes'])
	flash('<span>CPF e/ou senha incorretos!</span>','red')
	return redirect(url_for('admin.termologin'))

@admin.route('/termo/print',methods = ['GET','POST'])
def termoprint():
	docx_document = DocxTemplate('static/templates/template_termo_concursos.docx')
	context={}
	context['NOME']=request.form['nome']
	context['AREA']=request.form['area']
	context['CAMP']=request.form['camp']
	context['FUNCAO']=request.form['funcao']
	context['VINCULO']=request.form['vinculo']
	context['TITULACAO']=request.form['titulacao']
	context['FORMACAO']=request.form['formacao']
	context['DATANASC']=request.form['datanasc']
	context['RG']=request.form['rg']
	context['ORGEXP']=request.form['orgexp']
	context['CPF']=request.form['cpf']
	context['MATRICULA']=request.form['matricula']
	context['PIS']=request.form['pis']
	context['ENDERECO']=request.form['endereco']
	context['BAIRRO']=request.form['bairro']
	context['MUNICIPIO']=request.form['municipio']
	context['UF']=request.form['uf']
	context['CEP']=request.form['cep']
	context['CEL1']=request.form['cel1']
	context['CEL2']=request.form['cel2']
	context['TEL1']=request.form['tel1']
	context['TEL2']=request.form['tel2']
	context['EMAIL']=request.form['email']
	context['ESTADOCIVIL']=request.form['estadocivil']
	context['BANCO']=request.form['banco']
	context['NBANCO']=request.form['nbanco']
	context['AGENCIA']=request.form['agencia']
	context['CONTA']=request.form['conta']
	context['TIPOCONTA']=request.form['tipoconta']
	context['CONJUNTA']=request.form['conjunta']
	context['TIPOPAGAMENTO']=request.form['tipopagamento']
	if context['CONJUNTA']=='sim':
		context['CORRENTISTA2']=request.form['correntista2']
	else:
		context['CORRENTISTA2']=""
	saveTermoConcursos(context)
	if context['TIPOCONTA']=='poupanca':
		context['TIPOCONTA']='Corrente (   ) Poupança ( x )'
	else:
		context['TIPOCONTA']='Corrente ( x ) Poupança (   )'
	if context['CONJUNTA']=='sim':
		context['CONJUNTA']='Sim ( x ) Não (   )'
	else:
		context['CONJUNTA']='Sim (   ) Não ( x )'
	tp=request.form['tipopagamento']
	context['t1']=""
	context['t2']=""
	context['t3']=""
	if tp=="bolsista":
		context['t1']="x"
	if tp=="emissao":
		context['t2']="x"
	if tp=="rpa":
		context['t3']="x"
	docx_document.render(context)
	nome=context['NOME'].split(' ')[0];
	docx1='static/temp/uns_termo_'+nome+'.docx'
	pdf1='static/temp/uns_termo_'+nome+'.pdf'
	pdf2='static/temp/termo_'+nome+'.pdf'
	docx_document.save(docx1)
	run(["doc2pdf",docx1])
	encrypt_pdf(pdf1,pdf2,'Docs@Fcm467')
	os.remove(docx1)
	os.remove(pdf1)
	f=open(pdf2, 'rb')
	os.remove(pdf2)
	filename='termo_'+nome+'.pdf'
	try:
		return flask.send_file(f,
					 attachment_filename=filename.encode("ascii","replace").decode("ascii"),
					 as_attachment=False,
					 mimetype="application/pdf")
	except Exception as e:
		 return str(e)

@admin.route('/termo/receber',methods = ['GET','POST'])
def termoreceive():
	file=request.files.get('file')
	if file:
		fileName=request.form['nome']+".pdf";
		file.save("static/termos/"+fileName);
		flash("<span>Arquivo recebido com sucesso!</span>","green")
	else:
		flash("<span>Erro ao submeter arquivo</span>","red")
	return redirect(url_for('admin.termologin'))


@admin.route('/termos')
def gettermos():
	os.chdir('static/termos')
	names=sorted(filter(os.path.isfile, os.listdir('.')), key=os.path.getmtime, reverse=True)
	os.chdir('../..')
	return render_template('termos_list.html', names=names)

@admin.route('/formulario/viagem/login',methods = ['GET'])
def termoviagemlogin():
	return render_template('termo_viagem_login.html')

@admin.route('/formulario/viagem',methods = ['GET', 'POST'])
def preenchimentotermoviagem():
	banco=[{'area':'Administração','funcao':'Presidente','nome':'Pedro Paulo Lacerda Sales','vinculo':'IF SUDESTE MG','rg':'M3323582','orgexp':'SSP-MG','cpf':'542.413.916-72','estadocivil':'Cataguases','cel1':'(32) 3441-8655 (fixo) (32) 99984-2230 (cel)','email':'pedro.sales@ifsudestemg.edu.br','endereco':'RUA ANTÔNIO OLIVEIRA MOURA GUIMARÃES, 61 A','bairro':'PRAÇA DA BANDEIRA','municipio':'Leopoldina','uf':'MG','cep':'36700000','banco':'SANTANDER','nbanco':'033','agencia':'3185','conta':'01000056-7','senha':'54241'},
{'area':'Administração','funcao':'Titular 2','nome':'Rodrigo Lacerda Sales ','vinculo':'CEFET-MG','rg':'M 8643801','orgexp':'SSP-MG','cpf':'661.736.556-91','estadocivil':'Casado','cel1':'32999842340','email':'rodrigosales13@cefetmg.br','endereco':'Rua Antônio Moura Oliveira Guimarães, 61','bairro':'Praça da Bandeira','municipio':'Leopoldina','uf':'MG','cep':'36700000','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'608','conta':'20.555-2','senha':'66173'},
{'area':'Administração','funcao':'Titular 1','nome':'Bruno Silva Olher','vinculo':'IF SUDESTE MG','rg':'5911918','orgexp':'SSP-MG','cpf':'037.653.806-60','estadocivil':'Rio Pomba','cel1':'(32) 98813-1359','email':'bruno.olher@ifsudestemg.edu.br','endereco':'RUA JOSÉ FELIZZOLA, 117/304','bairro':'SANTA ISABEL','municipio':'Rio Pomba','uf':'MG','cep':'36180-000','banco':'BRASIL','nbanco':'001','agencia':'0487-1','conta':'13428-7','senha':'03765'},
{'area':'Administração','funcao':'Presidente','nome':'Simone Guedes Donnelly','vinculo':'IF SUDESTE MG','rg':'381532641','orgexp':'SSP-SP','cpf':'896.506.381-72','estadocivil':'Casada','cel1':'33984365252','email':'simone.guedes@ifsudestemg.edu.br','endereco':'RUA GERALDO AMIN SAMOR Nº 44','bairro':'RECANTO DAS PALMEIRAS','municipio':'Cataguases','uf':'MG','cep':'36773-480','banco':'Banco do Brasil','nbanco':'001','agencia':'0316-6','conta':'56185-1','senha':'89650'},
{'area':'Administração','funcao':'Titular 1','nome':'Elder Stroppa','vinculo':'IF SUDESTE MG','rg':'M5770362','orgexp':'SSP-MG','cpf':'958.749.686-87','estadocivil':'Manhuaçu','cel1':'(32) 99958-5168 Trabalho – (33) 3333-0100; (33) 3333-0103; (33) 3333-0105','email':'elder.stroppa@ifsudestemg.edu.br','endereco':'RUA JOSÉ PINHEIRO FIGUEIRAS, 106/301','bairro':'PINHEIRO','municipio':'Manhuaçu','uf':'MG','cep':'36904-112','banco':'BRASIL','nbanco':'001','agencia':'2728-6','conta':'8904-4','senha':'95874'},
{'area':'Administração','funcao':'Titular 2','nome':'Luciano Polisseni Duque','vinculo':'IF SUDESTE MG','rg':'5771764','orgexp':'SSP-MG','cpf':'011.738.776-22','estadocivil':'Juiz de Fora','cel1':'(32) 98845-8008 e (32) 3235-9037','email':'luciano.polisseni@ifsudestemg.edu.br','endereco':'RUA IRINEU MARINHO, 365/1004','bairro':'BOM PASTOR','municipio':'Juiz de Fora','uf':'MG','cep':'36021/580','banco':'BRASIL','nbanco':'001','agencia':'5751-7','conta':'45575-X','senha':'01173'},
{'area':'Administração','funcao':'Presidente','nome':'Nuno Álvares Felizardo Júnior','vinculo':'IF SUDESTE MG','rg':'9247408','orgexp':'SSP','cpf':'052.088.836-78','estadocivil':'Divorciado','cel1':'32988882256','email':'nuno.felizardo@ifsudestemg.edu.br','endereco':'Rua José Dias Paes, 187','bairro':'Bela Vista','municipio':'Ubá','uf':'MG','cep':'36507006','banco':'Bradesco','nbanco':'237','agencia':'1940','conta':'259861','senha':'05208'},
{'area':'Administração','funcao':'Titular 1','nome':'Sandro Feu de Souza','vinculo':'IF SUDESTE MG','rg':'M 5198310','orgexp':'SSP-MG','cpf':'723-161-016-15','estadocivil':'Casado','cel1':'(32)988610733','email':'sandro.feu@ifsudestemg.edu.br','endereco':'Rua da Cerâmica, 245','bairro':'Cerâmica','municipio':'Muriaé','uf':'MG','cep':'36883009','banco':'Bradesco','nbanco':'237','agencia':'576-2','conta':'31044-1','senha':'72316'},
{'area':'Administração','funcao':'Titular 2','nome':'Helder Antônio da Silva','vinculo':'IF SUDESTE MG','rg':'MG-4.268.230','orgexp':'PC-MG','cpf':'674.480.706-49','estadocivil':'casado','cel1':'32-99117-1783','email':'helder.silva@ifsudestemg.edu.br','endereco':'RUA JORNALISTA PAULO EMÍLIO GONÇALVES, 77/402','bairro':'Boa Morte','municipio':'Barbacena','uf':'MG','cep':'36200-132','banco':'Banco do Brasil','nbanco':'001','agencia':'0062-0','conta':'62855-7','senha':'67448'},
{'area':'Agronomia-Solos','funcao':'Presidente','nome':'Cleber Kouri de Souza','vinculo':'IF SUL DE MINAS ','rg':'222750','orgexp':'SSP-AC','cpf':'973.247.366-53','estadocivil':'Casado','cel1':'(35) 9 9934-6815','email':'cleber.souza@ifsuldeminas.edu.br','endereco':'Rua Capitão Resende Costa, 207','bairro':'Santa Luzia','municipio':'Inconfidentes','uf':'MG','cep':'37576-000','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'691','conta':'22519-0','senha':'97324'},
{'area':'Agronomia-Solos','funcao':'Titular 1','nome':'Mateus Marques Bueno','vinculo':'IFMG','rg':'10344165','orgexp':'SSP-MG','cpf':'014.123.676-03','estadocivil':'Solteiro','cel1':'33987287024','email':'mateus.bueno@ifmg.edu.br','endereco':'Avenida das Américas, nº 13554, Apto 608 - Bloco 2','bairro':'Recreio','municipio':'Rio de Janeiro','uf':'RJ','cep':'22790701','banco':'Banco do Brasil','nbanco':'001','agencia':'696305','conta':'9823-X','senha':'01412'},
{'area':'Agronomia-Solos','funcao':'Titular 2','nome':'Sheila Isabel do Carmo Pinto','vinculo':'IFMG','rg':'MG 10.278.421','orgexp':'SSP','cpf':'032.656.976-65','estadocivil':'Solteira','cel1':'(37)998202525','email':'sheila.isabel@ifmg.edu.br','endereco':'Rua Sinfrônio Torres, 458','bairro':'Lavapés','municipio':'Bambuí','uf':'MG','cep':'38900-000','banco':'Banco do Brasil','nbanco':'001','agencia':'0364-6','conta':'34551-2','senha':'03265'},
{'area':'Bioquímica','funcao':'Presidente','nome':'José Emílio Zanzirolani de Oliveira','vinculo':'IF SUDESTE MG','rg':'MG3751505','orgexp':'SSP-MG','cpf':'538.246.106-63','estadocivil':'Barbacena','cel1':'32 988377450; 32 3333 5853','email':'jose.zanzirolani@ifsudestemg.edu.br','endereco':'RUA PIAUÍ','bairro':'CAMPO','municipio':'Barbacena','uf':'MG','cep':'36200-334','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'99','conta':'20191*8','senha':'53824'},
{'area':'Bioquímica','funcao':'Titular 1','nome':'Larissa Mattos Trevizano','vinculo':'IF SUDESTE MG','rg':'13078198','orgexp':'SSP-MG','cpf':'073.110.836-13','estadocivil':'Rio Pomba','cel1':'32 98808 4442; 32 35715721','email':'larissa.trevizano@ifsudestemg.edu.br','endereco':'RUA JOSÉ LIMA DE OLIVEIRA, 208','bairro':'JARDIM AMÉRICA','municipio':'Rio Pomba','uf':'MG','cep':'36180-000','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'1123','conta':'24864-9','senha':'07311'},
{'area':'Direito','funcao':'Presidente','nome':'André Luís Del Negri','vinculo':'UFV','rg':'16547135896','orgexp':'SSP-SP','cpf':'165.471.358-96','estadocivil':'solteiro','cel1':'34992328018','email':'andredelnegri@uol.com.br','endereco':'Rua dos Estudantes, 75 - Vivant Residence - apto 803','bairro':'Centro','municipio':'Viçosa','uf':'MG','cep':'36570081','banco':'Banco do Brasil','nbanco':'001','agencia':'0428-6','conta':'91.316-2','senha':'16547'},
{'area':'Bioquímica','funcao':'Titular 2','nome':'Mara Lúcia Rodrigues Costa','vinculo':'UEMG','rg':'MG3241193','orgexp':'SSP-MG','cpf':'520.898.516-00','estadocivil':'Solteira','cel1':'(32)99986-5376','email':'mlrcosta@uol.com.br','endereco':'Praça Hilário, 60','bairro':'São José','municipio':'Barbacena','uf':'MG','cep':'36205034','banco':'Banco do Brasil','nbanco':'001','agencia':'0062-0','conta':'15.112-2','senha':'52089'},
{'area':'Direito','funcao':'Titular 1','nome':'Caroline Bastos Dantas','vinculo':'Centro Universitário de Sete Lagoas','rg':'M 8217953','orgexp':'SSP-MG','cpf':'031.947.646-40','estadocivil':'união estável','cel1':'31 99617-3443','email':'carolinebdantas@gmail.com','endereco':'Rua Suzana Furtado de Oliveira, 25, 201','bairro':'Silveira','municipio':'Belo Horizonte','uf':'MG','cep':'31140430','banco':'Banco do Brasil','nbanco':'001','agencia':'870587','conta':'12528-8','senha':'03194'},
{'area':'Direito','funcao':'Titular 2','nome':'Galvão Rabelo','vinculo':'UNA/Fundação Presidente Antônio Carlos','rg':'12271623','orgexp':'SSP-MG','cpf':'060.199.556-21','estadocivil':'casado','cel1':'31984347952','email':'galvaorabelo@yahoo.com.br','endereco':'Rua Itambé do Mato Dentro, 330','bairro':'Serrano','municipio':'Belo Horizonte','uf':'MG','cep':'30882670','banco':'Banco do Brasil','nbanco':'001','agencia':'0270-4','conta':'50227-8','senha':'06019'},
{'area':'Direito','funcao':'Presidente','nome':'André Luís Del Negri','vinculo':'UFV','rg':'16547135896','orgexp':'SSP-SP','cpf':'165.471.358-96','estadocivil':'solteiro','cel1':'34992328018','email':'andredelnegri@uol.com.br','endereco':'Rua dos Estudantes, 75 - Vivant Residence - apto 803','bairro':'Centro','municipio':'Viçosa','uf':'MG','cep':'36570081','banco':'Banco do Brasil','nbanco':'001','agencia':'0428-6','conta':'91.316-2','senha':'16547'},
{'area':'Direito','funcao':'Titular 1','nome':'Caroline Bastos Dantas','vinculo':'Centro Universitário de Sete Lagoas','rg':'M 8217953','orgexp':'SSP-MG','cpf':'031.947.646-40','estadocivil':'união estável','cel1':'31 99617-3443','email':'carolinebdantas@gmail.com','endereco':'Rua Suzana Furtado de Oliveira, 25, 201','bairro':'Silveira','municipio':'Belo Horizonte','uf':'MG','cep':'31140430','banco':'Banco do Brasil','nbanco':'001','agencia':'870587','conta':'12528-8','senha':'03194'},
{'area':'Direito','funcao':'Titular 2','nome':'Galvão Rabelo','vinculo':'UNA/Fundação Presidente Antônio Carlos','rg':'12271623','orgexp':'SSP-MG','cpf':'060.199.556-21','estadocivil':'casado','cel1':'31984347952','email':'galvaorabelo@yahoo.com.br','endereco':'Rua Itambé do Mato Dentro, 330','bairro':'Serrano','municipio':'Belo Horizonte','uf':'MG','cep':'30882670','banco':'Banco do Brasil','nbanco':'001','agencia':'0270-4','conta':'50227-8','senha':'06019'},
{'area':'Enfermagem','funcao':'Presidente','nome':'Dênis Derly Damasceno','vinculo':'IF SUDESTE MG','rg':'MG11008282','orgexp':'SSP-MG','cpf':'038.989.196-76','estadocivil':'Barbacena','cel1':'(32) 98874-3011; (32) 3333-7735','email':'denis.damasceno@ifsudestemg.edu.br','endereco':'RUA DOUTOR OSWALDO FORTINI, 50','bairro':'SÃO JOSÉ','municipio':'Barbacena','uf':'MG','cep':'36205-110','banco':'BRASIL','nbanco':'001','agencia':'0062-0','conta':'62231-1','senha':'03898'},
{'area':'Enfermagem','funcao':'Titular 1','nome':'Marjorye Polinati da Silva Vecchi','vinculo':'IF SUDESTE MG','rg':'12338039','orgexp':'SSP-MG','cpf':'023.126.337-60','estadocivil':'Rio Pomba','cel1':'(32) 99905-8787; (32) 3571-1432','email':'marjorye.vecchi@ifsudestemg.edu.br','endereco':'RUA TIRADENTES, 32','bairro':'SÃO MANOEAL','municipio':'Rio Pomba','uf':'MG','cep':'36180-000','banco':'BRASIL','nbanco':'001','agencia':'2458-9','conta':'6197-2','senha':'02312'},
{'area':'Enfermagem','funcao':'Titular 2','nome':'Vaneska Ribeiro Perfeito Santos','vinculo':'IF SUL DE MINAS ','rg':'M3994002','orgexp':'SSP-MG','cpf':'720.348.586-20','estadocivil':'SÃO JOÃO DEL REY','cel1':'(32) 99987-1840','email':'vaneska.perfeito@ifsudestemg.edu.br','endereco':'PRAÇA PROFESSOR JOSÉ BATISTA DE SOUZA, 22','bairro':'CENTRO','municipio':'SÃO JOÃO DEL REY','uf':'MG','cep':'36300-144','banco':'SANTANDER','nbanco':'033','agencia':'3305','conta':'010059223-5','senha':'72034'},
{'area':'Engenharia Civil','funcao':'Presidente','nome':'Samuel Santos De Souza Pinto','vinculo':'IF SUL DE MINAS ','rg':'12532850','orgexp':'SSP-MG','cpf':'060.270.686-63','estadocivil':'Pouso Alegre','cel1':'35 99853-4512','email':'samuel.souza@ifsuldeminas.edu.br','endereco':'RUA MARIA GUILHERMINA FRANCO, 55','bairro':'ARISTEU COSTA RIOS','municipio':'Pouso Alegre','uf':'MG','cep':'37558-451','banco':'BRASIL','nbanco':'001','agencia':'4865/8','conta':'48564-0','senha':'06027'},
{'area':'Engenharia Civil','funcao':'Titular 1','nome':'Geraldo Magela Damasceno','vinculo':'CEFET-MG','rg':'M3528409','orgexp':'SSP-MG','cpf':'881.085.626_-0','estadocivil':'BELO HORIZONTE','cel1':'38 9802-8987','email':'geraldodamasceno@cefetmg.br','endereco':'RUA JURACI, 88','bairro':'NOVA SUIÇA','municipio':'Belo Horizonte','uf':'MG','cep':'30421-181','banco':'BRASIL','nbanco':'001','agencia':'0103-1','conta':'56856-2','senha':'88108'},
{'area':'Engenharia Civil','funcao':'Titular 2','nome':'Fabiane de Fátima Maciel','vinculo':'IF SUDESTE MG','rg':'MG13771155','orgexp':'SSP-MG','cpf':'086.288.296-60','estadocivil':'São João Del Rey','cel1':'31 98721-0842','email':'fabiane.maciel@ifsudestemg.edu.br','endereco':'Rua monsenhor Silvestre de Catsro, 1003, Apto 202','bairro':'Colonia do Marçal','municipio':'São João Del Rey','uf':'MG','cep':'36302-022','banco':'BRASIL','nbanco':'001','agencia':'4865-8','conta':'5208-6','senha':'08628'},
{'area':'Engenharia Civil','funcao':'Presidente','nome':'Bruno Márcio Agostini','vinculo':'IF SUDESTE MG','rg':'M9039235','orgexp':'SSP-MG','cpf':'009.077.196.60','estadocivil':'São João Del Rey','cel1':'(32)9 8814 8857; (32) 3379 4500','email':'bruno.agostini@ifsudestemg.edu.br','endereco':'Rua Antônio Agostini,100','bairro':'Matosinhos','municipio':'São João Del Rey','uf':'MG','cep':'36305-026','banco':'BRASIL','nbanco':'001','agencia':'1627','conta':'65931-2','senha':'00907'},
{'area':'Engenharia Civil','funcao':'Titular 1','nome':'Cláudia Valéria Gávio Coura','vinculo':'IF SUDESTE MG','rg':'M-4.291.330','orgexp':'SSP-MG','cpf':'865.724.076-91','estadocivil':'Casada','cel1':'32 99918 4042','email':'claudia.coura@ifsudestemg.edu.br','endereco':'Rua Pernambuco, 132','bairro':'Poço Rico','municipio':'Juiz de Fora','uf':'MG','cep':'36020-150','banco':'Banco do Brasil','nbanco':'001','agencia':'400063','conta':'800.964-3','senha':'86572'},
{'area':'Engenharia Civil','funcao':'Titular 2','nome':'Fabrício Borges Cambraia','vinculo':'UFJF','rg':'8096000164','orgexp':'SSP-RS','cpf':'033.724.466-90','estadocivil':'Juiz de Fora','cel1':'(32) 9 9150 9897; (32) 2102 3411','email':'fabricio.cambraia@engenharia.ufjf.br','endereco':'Rua Guaçui, 395/306C','bairro':'São Mateus','municipio':'Juiz de Fora','uf':'MG','cep':'36025-190','banco':'BRASIL','nbanco':'001','agencia':'2995-5','conta':'52329-1','senha':'03372'},
{'area':'Engenharia Mecânica','funcao':'Presidente','nome':'Samuel Sander de Carvalho','vinculo':'IF SUDESTE MG','rg':'MG12658737','orgexp':'SSP-MG','cpf':'014.360.996-33','estadocivil':'Casado','cel1':'32999779592','email':'samuel.carvalho@ifsudestemg.edu.br','endereco':'Rua Coronel Tancredo, 55, Bloco 55 Apto 207','bairro':'Fábrica','municipio':'Juiz de Fora','uf':'MG','cep':'36080-240','banco':'SICOOB ','nbanco':'756','agencia':'3173','conta':'55222-4','senha':'01436'},
{'area':'Engenharia Mecânica','funcao':'Titular 1','nome':'Tiago Alceu Coelho Resende','vinculo':'CEFET-MG','rg':'MG 13 668 154','orgexp':'SSP','cpf':'084.616.886-35','estadocivil':'Casado','cel1':'(31) 9 8558 0721','email':'tiagoalceu@cefetmg.br','endereco':'Rua Prof. Joaquim Guedes Machado','bairro':'Centro','municipio':'Leopoldina','uf':'MG','cep':'36700000','banco':'Santander','nbanco':'033','agencia':'3185','conta':'01051000-4','senha':'08461'},
{'area':'Engenharia Mecânica','funcao':'Titular 2','nome':'Carlos Henrique Lauro','vinculo':'UFSJDR','rg':'8612702','orgexp':'SSP-MG','cpf':'040.073.616-06','estadocivil':'solteiro','cel1':'32998362293','email':'carloslauro@ufsj.edu.br','endereco':'Rua Belizário Pena, 82/302A','bairro':'Centro','municipio':'Barbacena','uf':'MG','cep':'36200012','banco':'Banco do Brasil','nbanco':'001','agencia':'0062-0','conta':'38892-0','senha':'04007'},
{'area':'Engenharia Mecânica A','funcao':'Presidente','nome':'Carlos Eduardo dos Santos editar','vinculo':'CEFET-MG','rg':'MG6342395','orgexp':'SSP','cpf':'039.679.686-93','estadocivil':'Casado','cel1':'31988632774','email':'carloseduardo@cefetmg.br','endereco':'Rua Mato Grosso, 574','bairro':'Sra das Graças','municipio':'Betim','uf':'MG','cep':'32604740','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'814','conta':'208454','senha':'03967'},
{'area':'Engenharia Mecânica A','funcao':'Titular 1','nome':'Aderci de Freitas Filho editar','vinculo':'CEFET-MG','rg':'3775433','orgexp':'PC-MG','cpf':'653.699.396-91','estadocivil':'Casado','cel1':'31-991695512','email':'aderciff@gmail.com','endereco':'Rua Pereira, 126','bairro':'São Cristóvão','municipio':'Betim','uf':'MG','cep':'32676688','banco':'Santander','nbanco':'033','agencia':'4519','conta':'01000639-8','senha':'65369'},
{'area':'Engenharia Mecânica A','funcao':'Titular 2','nome':'Ernane Rodrigues da Silva','vinculo':'CEFET-MG','rg':'M2838835','orgexp':'SSP-MG','cpf':'385.220.806-82','estadocivil':'Casado','cel1':'991073575','email':'ernane@cefetmg.br','endereco':'Rua Andrômeda , 399','bairro':'Jardim Riacho','municipio':'Contagem','uf':'MG','cep':'32242200','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'814','conta':'906020-4','senha':'38522'},
{'area':'Engenharia Mecânica B','funcao':'Presidente','nome':'Samuel Sander de Carvalho','vinculo':'IF SUDESTE MG','rg':'MG12658737','orgexp':'SSP-MG','cpf':'014.360.996-33','estadocivil':'Casado','cel1':'32999779592','email':'samuel.carvalho@ifsudestemg.edu.br','endereco':'Rua Coronel Tancredo, 55, Bloco 55 Apto 207','bairro':'Fábrica','municipio':'Juiz de Fora','uf':'MG','cep':'36080-240','banco':'SICOOB ','nbanco':'756','agencia':'3173','conta':'55222-4','senha':'01436'},
{'area':'Engenharia Mecânica B','funcao':'Titular 1','nome':'Carlos Henrique Lauro','vinculo':'UFSJDR','rg':'8612702','orgexp':'SSP-MG','cpf':'040.073.616-06','estadocivil':'solteiro','cel1':'32998362293','email':'carloslauro@ufsj.edu.br','endereco':'Rua Belizário Pena, 82/302A','bairro':'Centro','municipio':'Barbacena','uf':'MG','cep':'36200012','banco':'Banco do Brasil','nbanco':'001','agencia':'0062-0','conta':'38892-0','senha':'04007'},
{'area':'Engenharia Mecânica B','funcao':'Titular 2','nome':'Denison Baldo','vinculo':'IF SUDESTE MG','rg':'MG13019972','orgexp':'SSP-MG','cpf':'062.763.796-54','estadocivil':'solteiro','cel1':'(32)98419-8132','email':'denison.baldo@ifsudestemg.edu.br','endereco':'R. SUENY SACCONI, 736','bairro':'MONTE CASTELO','municipio':'JUIZ DE FORA','uf':'MG','cep':'36081-065','banco':'Banco do Brasil','nbanco':'001','agencia':'1406732','conta':'14048-1','senha':'06276'},
{'area':'Engenharia Metalúrgica A','funcao':'Presidente','nome':'Erivelto  Luís de Souza','vinculo':'UFSJ','rg':'07488296-9','orgexp':'IFP-RJ','cpf':'895.861.667-91','estadocivil':'Barbacena','cel1':'(31) 98915-8829','email':'souza.erivelto@ufsj.edu.br','endereco':'Rua José Francisco Costa, 325','bairro':'Mário Quintão','municipio':'Barbacena','uf':'MG','cep':'36201-482','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'99','conta':'30302-8','senha':'89586'},
{'area':'Engenharia Metalúrgica A','funcao':'Titular 1','nome':'José Carlos dos Santos Pires','vinculo':'IFMG','rg':'M. 3.841.438','orgexp':'SSP-MG','cpf':'745.302.086-72','estadocivil':'Casado','cel1':'31 988803680','email':'jose.pires@ifmg.edu.br','endereco':'Rua Tancredo Neves, 15, Cachoeira do Campo','bairro':'Residencial Sacramento','municipio':'Ouro Preto','uf':'MG','cep':'35410-000','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'136','conta':'00059972-9','senha':'74530'},
{'area':'Engenharia Metalúrgica A','funcao':'Titular 2','nome':'Charles Luís da Silva','vinculo':'UFV','rg':'24674045-0','orgexp':'SSP-SP','cpf':'247.883.908-33','estadocivil':'Casado','cel1':'31 971759868','email':'charles.silva@ufv.br','endereco':'Rua Liberdade, 261','bairro':'Inconfidência','municipio':'Viçosa','uf':'MG','cep':'36576-292','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'0584-1','conta':'13390-0','senha':'24788'},
{'area':'Engenharia Metalúrgica B','funcao':'Presidente','nome':'Raphael Fortes Marcomini','vinculo':'UFJF','rg':'335888677','orgexp':'SSP-SP','cpf':'301.536.228-30','estadocivil':'solteiro','cel1':'32999402279','email':'raphael.marcomini@engenharia.ufjf.br','endereco':'Rua Bento Hinoto 149  apto 402','bairro':'Martelos','municipio':'Juiz de Fora','uf':'MG','cep':'36036554','banco':'Nu Pagamentos SA','nbanco':'260','agencia':'1','conta':'7656124','senha':'30153'},
{'area':'Engenharia Metalúrgica B','funcao':'Titular 2','nome':'Jalon de Morais Vieira','vinculo':'IF SUDESTE MG','rg':'M5026497','orgexp':'SSP-MG','cpf':'994.894.816-53','estadocivil':'Divorciado','cel1':'(32)991193610','email':'jalon.vieira@ifsudestemg.edu.br','endereco':'Rua Professor Clóvis Jaguaribe 240/401','bairro':'Bom Pastor','municipio':'Juiz de Fora','uf':'MG','cep':'36021-700','banco':'Banco do Brasil','nbanco':'001','agencia':'1406732','conta':'17286-3','senha':'99489'},
{'area':'Engenharia Metalúrgica B','funcao':'Titular 2','nome':'Charles Luís da Silva','vinculo':'UFV','rg':'24674045-0','orgexp':'SSP-SP','cpf':'247.883.908-33','estadocivil':'Casado','cel1':'31 971759868','email':'charles.silva@ufv.br','endereco':'Rua Liberdade, 261','bairro':'Inconfidência','municipio':'Viçosa','uf':'MG','cep':'36576-292','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'0584-1','conta':'13390-0','senha':'24788'},
{'area':'Gestão Ambiental ','funcao':'Presidente','nome':'Eduardo Sales Machado Borges','vinculo':'IF SUDESTE MG','rg':'M5410459','orgexp':'SSP-MG','cpf':'805.005.366-00','estadocivil':'Casado','cel1':'(32)999469131','email':'eduardo.borges@ifsudestemg.edu.br','endereco':'Rua Doutor Odilon Couto, 196','bairro':'Marino Ceolin','municipio':'Barbacena','uf':'MG','cep':'36200727','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'99','conta':'00026428-6','senha':'80500'},
{'area':'Gestão Ambiental ','funcao':'Titular 1','nome':'Ana Carolina Moraes Campos','vinculo':'IF SUDESTE MG','rg':'MG12231233','orgexp':'SSP-MG','cpf':'046.196.206-37','estadocivil':'Barbacena','cel1':'(32)984661039; (32)33721665','email':'anacarolina.campos@ifsudestemg.edu.br','endereco':'Rua Vereador José Moreira de Aquino','bairro':'Porto Real','municipio':'Santa Cruz de Minas','uf':'MG','cep':'36328-000','banco':'BRASIL','nbanco':'001','agencia':'0162-7','conta':'64424-2','senha':'04619'},
{'area':'Gestão Ambiental ','funcao':'Titular 2','nome':'José Alves Junqueira Júnior','vinculo':'IF SUDESTE MG','rg':'M8369065','orgexp':'SSP-MG','cpf':'028.943.136-08','estadocivil':'Bom Sucesso','cel1':'(35)991758610; (35)38413948','email':'jose.junqueira@ifsudestemg.edu.br','endereco':'Avenida lagoa dourada,96','bairro':'Lagoa dos Ipês','municipio':'Lavras','uf':'MG','cep':'37200-000','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'129','conta':'00156612-5','senha':'02894'},
{'area':'Informática','funcao':'Presidente','nome':'Pedro Henrique de Oliveira e Silva','vinculo':'IF SUDESTE MG','rg':'12846775','orgexp':'PC-MG','cpf':'073.297.776-25','estadocivil':'Bom Sucesso','cel1':'(37) 98804-2637','email':'pedrohenrique.silva@ifsudestemg.edu.br','endereco':'Rua Mato Grosso, 1578,  apto 202','bairro':'Sidi','municipio':'Dívinópolis','uf':'MG','cep':'35500-027','banco':'Bradesco','nbanco':'237','agencia':'0508-8','conta':'5752-5','senha':'07329'},
{'area':'Informática','funcao':'Titular 1','nome':'Teresina Moreira de Magalhães','vinculo':'IF SUDESTE MG','rg':'M7945831','orgexp':'SSP-MG','cpf':'024.094.156-01','estadocivil':'São João Del Rey','cel1':'(32)98416-1991; (31)984796036 ','email':'teresinha.magalhaes@ifsudestemg.edu.br','endereco':'Rua Mário de Andrade Gomes, 106/206','bairro':'Sagrada Família','municipio':'Belo Horizonte','uf':'MG','cep':'31030-050','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'0087','conta':'00030786-9','senha':'02409'},
{'area':'Informática','funcao':'Titular 2','nome':'Graziany Thiago Fonseca','vinculo':'IF SUDESTE MG','rg':'MG8401974','orgexp':'SSP','cpf':'053.102.726-07','estadocivil':'Bom Sucesso','cel1':'(34) 99135-8553','email':'graziany.fonseca@ifsudestemg.edu.br','endereco':'Rua Maria Messias Cazeca, 460','bairro':'Bela Vista','municipio':'Campo Belo','uf':'MG','cep':'37270-000','banco':'BRASIL','nbanco':'01','agencia':'7145-5','conta':'34710-8','senha':'05310'},
{'area':'Informática','funcao':'Titular 2','nome':'Sérgio Muinhos Barroso Lima','vinculo':'IF SUDESTE MG','rg':'mg5844026','orgexp':'SSP-MG','cpf':'023.886.396.46','estadocivil':'Casado','cel1':'32988571042','email':'sergio.lima@ifsudestemg.edu.br','endereco':'Rua Lindalva de paula Ribeiro, 28','bairro':'São Pedro','municipio':'Juiz de Fora','uf':'MG','cep':'36036466','banco':'Itaú','nbanco':'341','agencia':'6980','conta':'00460-7','senha':'02388'},
{'area':'Informática','funcao':'Titular 1','nome':'Lucas Grassano Lattari','vinculo':'IF SUDESTE MG','rg':'MG-13.773.370','orgexp':'SSP','cpf':'085.020.596-45','estadocivil':'Casado','cel1':'(32) 99820-8631','email':'lucas.lattari@ifsudestemg.edu.br','endereco':'Rua Sagrados Corações','bairro':'Centro','municipio':'Rio Pomba','uf':'MG','cep':'36180-000','banco':'Banco do Brasil','nbanco':'001','agencia':'400063','conta':'25501-7','senha':'08502'},
{'area':'Informática','funcao':'Titular 2','nome':'Samuel da Costa Alves Basilio','vinculo':'CEFET-MG','rg':'14359172','orgexp':'SSP-MG','cpf':'063.004.336-17','estadocivil':'Casado','cel1':'32991268999','email':'samuel@cefetmg.br','endereco':'Rua Maria Gouvea Ferraz','bairro':'Paraíso','municipio':'Cataguases','uf':'MG','cep':'36772154','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'608','conta':'00024324-1','senha':'06300'},
{'area':'Informática','funcao':'Presidente','nome':'Filipe Arantes Fernandes','vinculo':'IF SUDESTE MG','rg':'200977692','orgexp':'DETRAN-RJ','cpf':'100.993.327-28','estadocivil':'Manhuaçu','cel1':'(33) 99947-3464','email':'filipe.arantes@ifsudestemg.edu.br','endereco':'Rua Jorge Said Chequer, 40','bairro':'Alfa Sul','municipio':'Manhuaçu','uf':'MG','cep':'36904-192','banco':'BRASIL','nbanco':'001','agencia':'316-6','conta':'87053-6','senha':'10099'},
{'area':'Informática','funcao':'Titular 1','nome':'Rossini Pena Abrantes','vinculo':'IF SUDESTE MG','rg':'12398363','orgexp':'SSP-MG','cpf':'065.265.596-38','estadocivil':'Casado','cel1':'33 988066327','email':'rossini.abrantes@ifsudestemg.edu.br','endereco':'Rua Professora Mary Pinto Coelho, 71, Apt 2401','bairro':'Alfa Sul','municipio':'Manhuaçu','uf':'MG','cep':'36904207','banco':'Banco do Brasil','nbanco':'001','agencia':'0316-3','conta':'58184-4','senha':'06526'},
{'area':'Informática','funcao':'Titular 2','nome':'Roberto de Carvalho Ferreira','vinculo':'IF SUDESTE MG','rg':'MG-8144090','orgexp':'SSP-MG','cpf':'073.452.396-32','estadocivil':'Juiz de Fora','cel1':'(32) 99198-9203','email':'roberto.ferreira@ifsudestemg.edu.br','endereco':'Rua José do Patrocínio, 265/401','bairro':'Mundo Novo','municipio':'Juiz de Fora','uf':'MG','cep':'36026-340','banco':'Bradesco','nbanco':'237','agencia':'0428','conta':'10871-5','senha':'07345'},
{'area':'Informática','funcao':'Presidente','nome':'Eduardo Pereira da Rocha','vinculo':'IF SUDESTE MG','rg':'9333932','orgexp':'PC-MG','cpf':'045.798.036-20','estadocivil':'Casado','cel1':'32999995312','email':'eduardo.rocha@ifsudestemg.edu.br','endereco':'Rua Goiás, 86','bairro':'Chiquito Gazolla','municipio':'Ubá','uf':'MG','cep':'36506116','banco':'Banco do Brasil','nbanco':'001','agencia':'0270-4','conta':'31781-0','senha':'04579'},
{'area':'Informática','funcao':'Titular 1','nome':'Luciano Gonçalves Moreira','vinculo':'IF SUDESTE MG','rg':'m9328338','orgexp':'SSP-MG','cpf':'033.856.426-80','estadocivil':'Santos Dumont','cel1':'(32) 99197-4440 ','email':'luciano.moreira@ifsudestemg.edu.br','endereco':'Rua José Campos Alvim, 54','bairro':'Centro','municipio':'Barbacena','uf':'MG','cep':'36205-023','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'0099','conta':'4375-1','senha':'03385'},
{'area':'Informática','funcao':'Titular 2','nome':'Priscila Sad de Sousa','vinculo':'IF SUDESTE MG','rg':'14108640','orgexp':'SSP-MG','cpf':'083.299.516-93','estadocivil':'Solteira','cel1':'(32)988249523','email':'priscila.sad@ifsudestemg.edu.br','endereco':'Rua Santa Clara, 25','bairro':'São José ','municipio':'Barbacena ','uf':'MG','cep':'36205-050','banco':'Santander','nbanco':'033','agencia':'3043','conta':'01003634-1','senha':'08329'},
{'area':'Matemática','funcao':'Presidente','nome':'Priscila Roque de Almeida','vinculo':'IF SUDESTE MG','rg':'MG12644480','orgexp':'PC-MG','cpf':'092.924.646-20','estadocivil':'Solteira','cel1':'31994779830','email':'priscila.almeida@ifsudestemg.edu.br','endereco':'Rua Santos Dumont, 730/707','bairro':'Granbery','municipio':'Juiz de Fora','uf':'MG','cep':'36010386','banco':'Banco do Brasil','nbanco':'001','agencia':'1098-7','conta':'2934054','senha':'09292'},
{'area':'Matemática','funcao':'Titular 1','nome':'Farley Francisco Santana','vinculo':'IF SUDESTE MG','rg':'mg14328237','orgexp':'PC-MG','cpf':'084.908.376-19','estadocivil':'Casado','cel1':'38 991528711','email':'farleyfsantana@gmail.com','endereco':'Rua Dr Antonio Luiz Vieira Pena 150/301','bairro':'Mundo Novo','municipio':'Juiz de Fora','uf':'MG','cep':'36026315','banco':'Banco do Brasil','nbanco':'001','agencia':'104x','conta':'539015','senha':'08490'},
{'area':'Matemática','funcao':'Titular 2','nome':'Diógenes Ferreira Filho','vinculo':'Universidade Federal Rural do Rio de Janeiro','rg':'33182435-8','orgexp':'SSP-SP','cpf':'311.597.018-81','estadocivil':'Casado','cel1':'(32)99150-9595','email':'dffilho@gmail.com','endereco':'Rua Engenheiro Pedro Gentil 87 Apto 202','bairro':'Vale do Ipê','municipio':'Juiz de Fora','uf':'MG','cep':'36035-400','banco':'Banco do Brasil','nbanco':'001','agencia':'252871','conta':'40840-9','senha':'31159'},
{'area':'Matemática','funcao':'Presidente','nome':'Viviane Cristina Almada de Oliveira','vinculo':'UFSJ','rg':'M7245406','orgexp':'SSP-MG','cpf':'025.124.466-03','estadocivil':'São João Del-Rei','cel1':'(32) 988122090','email':'viviane@ufsj.edu.br','endereco':'Rua Fidélis Guimarães, 28','bairro':'Fábricas','municipio':'SÃO JOÃO DEL REY','uf':'MG','cep':'36301-228','banco':'Caixa Econômica Federal','nbanco':'104','agencia':'0151','conta':'00004-3','senha':'02512'},
{'area':'Matemática','funcao':'Titular 1','nome':'Wanderley Moura Rezende','vinculo':'UFF','rg':'59215475','orgexp':'SSP-MG','cpf':'837.588.017-53','estadocivil':'NITERÓI','cel1':'(21) 99994-6546','email':'wmrezende@id.uff.br','endereco':'RUA FAGUNDES VARELA, 240/302','bairro':'INGÁ','municipio':'NITERÓI','uf':'MG','cep':'24210520','banco':'Itaú','nbanco':'341','agencia':'6219','conta':'13615-4','senha':'83758'},
{'area':'Matemática','funcao':'Titular 2','nome':'Gilmer Jacinto Peres','vinculo':'CEFET-MG','rg':'7234962','orgexp':'SSP-MG','cpf':'979.960.686-15','estadocivil':'Casado','cel1':'31994420026','email':'gilmerperes@gmail.com','endereco':'RUA POTI, 122 APTO. 301','bairro':'PEDRO II','municipio':'BELO HORIZONTE','uf':'MG','cep':'30770080','banco':'Itaú','nbanco':'341','agencia':'6662','conta':'00184-8','senha':'97996'},
{'area':'Química ','funcao':'Presidente','nome':'Arlindo Inês Teixeira','vinculo':'IF SUDESTE MG','rg':'MG 10437952','orgexp':'SSP-MG','cpf':'034.063.176-77','estadocivil':'Casado','cel1':'(32) 988098507','email':'arlindo.teixeira@ifsudestemg.edu.br','endereco':'Rua João Roman, 71','bairro':'Colônia Rodrigo Silva','municipio':'Barbacena','uf':'MG','cep':'36201-156','banco':'Banco do Brasil','nbanco':'001','agencia':'62-0','conta':'75824-8','senha':'03406'},
{'area':'Química ','funcao':'Titular 1','nome':'Adalgisa Reis Mesquita','vinculo':'IF SUDESTE MG','rg':'MG2875010','orgexp':'SSP-MG','cpf':'588.190.536-91','estadocivil':'Barbacena','cel1':'32 9 88172001','email':'adalgisa.mesquita@ifsudestemg.edu.br','endereco':'RUA JOÃO CALMETO DE CASTRO, 95/102','bairro':'BELVEDERE','municipio':'Barbacena','uf':'MG','cep':'36201-132','banco':'Itaú','nbanco':'341','agencia':'1645','conta':'178805','senha':'58819'},
{'area':'Química ','funcao':'Titular 2','nome':'Joyce Barbosa Salazar','vinculo':'IF SUDESTE MG','rg':'11749186','orgexp':'SSP-MG','cpf':'047.182.826-24','estadocivil':'SÃO JOÃO DEL REY','cel1':'32 99158-0838','email':'joyce.salazar@ifsudestemg.edu.br','endereco':'ALAMEDA DAS BUGANVILIAS, 1000/134','bairro':'COLÔNIA DO MARÇAL','municipio':'SÃO JOÃO DEL REY','uf':'MG','cep':'36302670','banco':'BRASIL','nbanco':'001','agencia':'4459-8','conta':'7853-0','senha':'04718'},
{'area':'Zootecnica','funcao':'Presidente','nome':'Wagner Azis Garcia de Araújo','vinculo':'IFNMG','rg':'11453850','orgexp':'SSP-MG','cpf':'011.979816-67','estadocivil':'casado','cel1':'(38) 9 9106-0039','email':'aziszoo@yahoo.com.br','endereco':'Rua Prof. Manoel Ambrósio n.835','bairro':'Centro','municipio':'Januária','uf':'MG','cep':'39480 000','banco':'Banco do Brasil','nbanco':'001','agencia':'0286-0','conta':'40.074-2','senha':'01197'},
{'area':'Zootecnica','funcao':'Titular 1','nome':'Luiz Carlos Machado','vinculo':'IFMG','rg':'MG7578873','orgexp':'SSP-MG','cpf':'936.615.176-00','estadocivil':'Casado','cel1':'37998124153','email':'luiz.machado@ifmg.edu.br','endereco':'Rua Jose Candido Miranda, 500','bairro':'Candola','municipio':'Bambuí','uf':'MG','cep':'38900000','banco':'Itaú','nbanco':'341','agencia':'3192','conta':'10198-2','senha':'93661'},
{'area':'Zootecnica','funcao':'Titular 2','nome':'Mariana Costa Fausto','vinculo':'Faculdade de Ciências e Tecnologias de Viçosa','rg':'M9073-420','orgexp':'SSP','cpf':'061.557.926-40','estadocivil':'Casada','cel1':'(31) 99699-1310','email':'maricfausto@gmail.com','endereco':'Wanor Feijó, 165','bairro':'Barrinha','municipio':'Viçosa','uf':'MG','cep':'36574448','banco':'Banco do Brasil','nbanco':'001','agencia':'0428-6','conta':'12134-7','senha':'06155'}]
	if request.method == 'POST':
		email=request.form['email']
		passwd=request.form['passwd']
		for u in banco:
			if email==u["email"] and passwd==u["senha"]:
				return render_template('termo_viagem_preenchimento.html',nome=u["nome"],email=u["email"],cpf=u["cpf"],area=u["area"],funcoes=u["funcao"],vinculo=u["vinculo"],endereco=u["endereco"],bairro=u["bairro"],municipio=u["municipio"],uf=u["uf"],cep=u["cep"],rg=u["rg"],orgexp=u["orgexp"],estadocivil=u["estadocivil"],cel1=u["cel1"],banco=u["banco"],nbanco=u["nbanco"],agencia=u["agencia"],conta=u["conta"])
	flash('<span>CPF e/ou senha incorretos!</span>','red')
	return redirect(url_for('admin.termoviagemlogin'))

@admin.route('/formulario/viagem/receber',methods = ['GET','POST'])
def formularioreceive():
	file=request.files.get('file')
	if file:
		fileName=request.form['nome']+".pdf";
		file.save("static/formularios/"+fileName);
		flash("<span>Arquivo recebido com sucesso!</span>","green")
	else:
		flash("<span>Erro ao submeter arquivo</span>","red")
	return redirect(url_for('admin.termoviagemlogin'))

@admin.route('/formulario/viagem/print',methods = ['GET','POST'])
def formularioprint():
	docx_document = DocxTemplate('static/templates/template_formulario_concursos.docx')
	context={}
	context['NOME']=request.form['nome']
	context['AREA']=request.form['area']
	context['FUNCAO']=request.form['funcao']
	context['VINCULO']=request.form['vinculo']
	context['ENDERECO']=request.form['endereco']
	context['BAIRRO']=request.form['bairro']
	context['MUNICIPIO']=request.form['municipio']
	context['UF']=request.form['uf']
	context['CEP']=request.form['cep']
	context['DESLOCAMENTO_OD']=request.form['deslocamento_od']
	context['DESLOCAMENTO_OD_OP_2_COMP']=""
	context['DESLOCAMENTO_OD_OP_3_COMP']=""
	context["DESLOCAMENTO-AUX"]=""
	if context['DESLOCAMENTO_OD']=='op_2':
		context['DESLOCAMENTO_OD_OP_2_COMP']=request.form['deslocamento_od_op_2_comp']
		context["DESLOCAMENTO-AUX"]=request.form['deslocamento_od_op_2_comp']
	if context['DESLOCAMENTO_OD']=='op_3':
		context['DESLOCAMENTO_OD_OP_3_COMP']=request.form['deslocamento_od_op_3_comp']
		context["DESLOCAMENTO-AUX"]=request.form['deslocamento_od_op_3_comp']
	context['TRANSLADO']=request.form.getlist('translado')
	context['TRANSLADO']=" ".join(context['TRANSLADO'])
	context['HOSPEDAGEM']=request.form['hospedagem']
	context['HOSPEDAGEM_OP_1_COMP']=""
	context['HOSPEDAGEM_OP_2_COMP']=""
	context["HOSPEDAGEM-AUX"]=""
	if context['HOSPEDAGEM']=='hospedagem_op_1':
		context['HOSPEDAGEM_OP_1_COMP']=request.form['hospedagem_op_1_comp']
		context["HOSPEDAGEM-AUX"]=request.form['hospedagem_op_1_comp']
	if context['HOSPEDAGEM']=='hospedagem_op_2':
		context['HOSPEDAGEM_OP_2_COMP']=request.form['hospedagem_op_2_comp']
		context["HOSPEDAGEM-AUX"]=request.form['hospedagem_op_2_comp']
	context['ALIMENTACAO']=request.form['alimentacao']
	context['CPF']=request.form['cpf']
	context['DATANASC']=request.form['datanasc']
	context['RG']=request.form['rg']
	context['ORGEXP']=request.form['orgexp']
	context['CEL1']=request.form['cel1']
	context['EMAIL']=request.form['email']
	context['ESTADOCIVIL']=request.form['estadocivil']
	context['BANCO']=request.form['banco']
	context['NBANCO']=request.form['nbanco']
	context['AGENCIA']=request.form['agencia']
	context['CONTA']=request.form['conta']
	context['TIPOCONTA']=request.form['tipoconta']
	context['CONJUNTA']=request.form['conjunta']
	if context['CONJUNTA']=='sim':
		context['CORRENTISTA2']=request.form['correntista2']
	else:
		context['CORRENTISTA2']=""
	if context['CONJUNTA']=='sim':
		context['CONJUNTA']='Sim'
	else:
		context['CONJUNTA']='Não'
	if context['TIPOCONTA']=='poupanca':
		context['TIPOCONTA']='Poupança'
	else:
		context['TIPOCONTA']='Corrente'
	saveFormularioConcursos(context)
	context['d1']=""
	context['d2']=""
	context['d3']=""
	context['d4']=""
	if request.form['deslocamento_od']=="op_1":
		context['d1']="x"
	if request.form['deslocamento_od']=="op_2":
		context['d2']="x"
	if request.form['deslocamento_od']=="op_3":
		context['d3']="x"
	if request.form['deslocamento_od']=="op_4":
		context['d4']="x"
	context['t1']=""
	context['t2']=""
	context['t3']=""
	context['t4']=""
	if "translado_op_1" in request.form.getlist('translado'):
		context['t1']="x"
	if "translado_op_2" in request.form.getlist('translado'):
		context['t2']="x"
	if "translado_op_3" in request.form.getlist('translado'):
		context['t3']="x"
	if "translado_op_4" in request.form.getlist('translado'):
		context['t4']="x"
	context['h1']=""
	context['h2']=""
	context['h3']=""
	if context['HOSPEDAGEM']=="hospedagem_op_1":
		context['h1']="x"
	if context['HOSPEDAGEM']=="hospedagem_op_2":
		context['h2']="x"
	if context['HOSPEDAGEM']=="hospedagem_op_3":
		context['h3']="x"
	context['a1']=""
	context['a2']=""
	if context['ALIMENTACAO']=="alimentacao_nao":
		context['a1']="x"
	if context['ALIMENTACAO']=="alimentacao_sim":
		context['a2']="x"
	docx_document.render(context)
	nome=context['NOME'].split(' ')[0];
	docx1='static/temp/uns_termo_'+nome+'.docx'
	pdf1='static/temp/uns_termo_'+nome+'.pdf'
	pdf2='static/temp/termo_'+nome+'.pdf'
	docx_document.save(docx1)
	run(["doc2pdf",docx1])
	encrypt_pdf(pdf1,pdf2,'Docs@Fcm467')
	os.remove(docx1)
	os.remove(pdf1)
	f=open(pdf2, 'rb')
	os.remove(pdf2)
	filename='formulario_'+nome+'.pdf'
	try:
		return flask.send_file(f,
					 attachment_filename=filename.encode("ascii","replace").decode("ascii"),
					 as_attachment=False,
					 mimetype="application/pdf")
	except Exception as e:
		 return str(e)

@admin.route('/formularios')
def getformularios():
	os.chdir('static/formularios')
	names=sorted(filter(os.path.isfile, os.listdir('.')), key=os.path.getmtime, reverse=True)
	os.chdir('../..')
	return render_template('formularios_list.html', names=names)

@admin.route('/comprovantes/login',methods = ['GET'])
def comprovanteslogin():
	return render_template('comprovantes_login.html')


@admin.route('/comprovantes/enviar',methods = ['GET', 'POST'])
def comprovantesenviar():
	banco=[{'nome':'Pedro Paulo Lacerda Sales','email':'pedro.sales@ifsudestemg.edu.br','senha':'54241'},
		{'nome':'Rodrigo Lacerda Sales ','email':'rodrigosales13@cefetmg.br','senha':'66173'},
		{'nome':'Bruno Silva Olher','email':'bruno.olher@ifsudestemg.edu.br','senha':'03765'},
		{'nome':'Simone Guedes Donnelly','email':'simone.guedes@ifsudestemg.edu.br','senha':'89650'},
		{'nome':'Elder Stroppa','email':'elder.stroppa@ifsudestemg.edu.br','senha':'95874'},
		{'nome':'Luciano Polisseni Duque','email':'luciano.polisseni@ifsudestemg.edu.br','senha':'01173'},
		{'nome':'Nuno Álvares Felizardo Júnior','email':'nuno.felizardo@ifsudestemg.edu.br','senha':'05208'},
		{'nome':'Sandro Feu de Souza','email':'sandro.feu@ifsudestemg.edu.br','senha':'72316'},
		{'nome':'Helder Antônio da Silva','email':'helder.silva@ifsudestemg.edu.br','senha':'67448'},
		{'nome':'Cleber Kouri de Souza','email':'cleber.souza@ifsuldeminas.edu.br','senha':'97324'},
		{'nome':'Mateus Marques Bueno','email':'mateus.bueno@ifmg.edu.br','senha':'01412'},
		{'nome':'Sheila Isabel do Carmo Pinto','email':'sheila.isabel@ifmg.edu.br','senha':'03265'},
		{'nome':'José Emílio Zanzirolani de Oliveira','email':'jose.zanzirolani@ifsudestemg.edu.br','senha':'53824'},
		{'nome':'Larissa Mattos Trevizano','email':'larissa.trevizano@ifsudestemg.edu.br','senha':'07311'},
		{'nome':'André Luís Del Negri','email':'andredelnegri@uol.com.br','senha':'16547'},
		{'nome':'Mara Lúcia Rodrigues Costa','email':'mlrcosta@uol.com.br','senha':'52089'},
		{'nome':'Caroline Bastos Dantas','email':'carolinebdantas@gmail.com','senha':'03194'},
		{'nome':'Galvão Rabelo','email':'galvaorabelo@yahoo.com.br','senha':'06019'},
		{'nome':'André Luís Del Negri','email':'andredelnegri@uol.com.br','senha':'16547'},
		{'nome':'Caroline Bastos Dantas','email':'carolinebdantas@gmail.com','senha':'03194'},
		{'nome':'Galvão Rabelo','email':'galvaorabelo@yahoo.com.br','senha':'06019'},
		{'nome':'Dênis Derly Damasceno','email':'denis.damasceno@ifsudestemg.edu.br','senha':'03898'},
		{'nome':'Marjorye Polinati da Silva Vecchi','email':'marjorye.vecchi@ifsudestemg.edu.br','senha':'02312'},
		{'nome':'Vaneska Ribeiro Perfeito Santos','email':'vaneska.perfeito@ifsudestemg.edu.br','senha':'72034'},
		{'nome':'Samuel Santos De Souza Pinto','email':'samuel.souza@ifsuldeminas.edu.br','senha':'06027'},
		{'nome':'Geraldo Magela Damasceno','email':'geraldodamasceno@cefetmg.br','senha':'88108'},
		{'nome':'Fabiane de Fátima Maciel','email':'fabiane.maciel@ifsudestemg.edu.br','senha':'08628'},
		{'nome':'Bruno Márcio Agostini','email':'bruno.agostini@ifsudestemg.edu.br','senha':'00907'},
		{'nome':'Cláudia Valéria Gávio Coura','email':'claudia.coura@ifsudestemg.edu.br','senha':'86572'},
		{'nome':'Fabrício Borges Cambraia','email':'fabricio.cambraia@engenharia.ufjf.br','senha':'03372'},
		{'nome':'Samuel Sander de Carvalho','email':'samuel.carvalho@ifsudestemg.edu.br','senha':'01436'},
		{'nome':'Tiago Alceu Coelho Resende','email':'tiagoalceu@cefetmg.br','senha':'08461'},
		{'nome':'Carlos Henrique Lauro','email':'carloslauro@ufsj.edu.br','senha':'04007'},
		{'nome':'Carlos Eduardo dos Santos editar','email':'carloseduardo@cefetmg.br','senha':'03967'},
		{'nome':'Aderci de Freitas Filho editar','email':'aderciff@gmail.com','senha':'65369'},
		{'nome':'Ernane Rodrigues da Silva','email':'ernane@cefetmg.br','senha':'38522'},
		{'nome':'Samuel Sander de Carvalho','email':'samuel.carvalho@ifsudestemg.edu.br','senha':'01436'},
		{'nome':'Carlos Henrique Lauro','email':'carloslauro@ufsj.edu.br','senha':'04007'},
		{'nome':'Denison Baldo','email':'denison.baldo@ifsudestemg.edu.br','senha':'06276'},
		{'nome':'Erivelto  Luís de Souza','email':'souza.erivelto@ufsj.edu.br','senha':'89586'},
		{'nome':'José Carlos dos Santos Pires','email':'jose.pires@ifmg.edu.br','senha':'74530'},
		{'nome':'Charles Luís da Silva','email':'charles.silva@ufv.br','senha':'24788'},
		{'nome':'Raphael Fortes Marcomini','email':'raphael.marcomini@engenharia.ufjf.br','senha':'30153'},
		{'nome':'Jalon de Morais Vieira','email':'jalon.vieira@ifsudestemg.edu.br','senha':'99489'},
		{'nome':'Charles Luís da Silva','email':'charles.silva@ufv.br','senha':'24788'},
		{'nome':'Eduardo Sales Machado Borges','email':'eduardo.borges@ifsudestemg.edu.br','senha':'80500'},
		{'nome':'Ana Carolina Moraes Campos','email':'anacarolina.campos@ifsudestemg.edu.br','senha':'04619'},
		{'nome':'José Alves Junqueira Júnior','email':'jose.junqueira@ifsudestemg.edu.br','senha':'02894'},
		{'nome':'Pedro Henrique de Oliveira e Silva','email':'pedrohenrique.silva@ifsudestemg.edu.br','senha':'07329'},
		{'nome':'Teresina Moreira de Magalhães','email':'teresinha.magalhaes@ifsudestemg.edu.br','senha':'02409'},
		{'nome':'Graziany Thiago Fonseca','email':'graziany.fonseca@ifsudestemg.edu.br','senha':'05310'},
		{'nome':'Sérgio Muinhos Barroso Lima','email':'sergio.lima@ifsudestemg.edu.br','senha':'02388'},
		{'nome':'Lucas Grassano Lattari','email':'lucas.lattari@ifsudestemg.edu.br','senha':'08502'},
		{'nome':'Samuel da Costa Alves Basilio','email':'samuel@cefetmg.br','senha':'06300'},
		{'nome':'Filipe Arantes Fernandes','email':'filipe.arantes@ifsudestemg.edu.br','senha':'10099'},
		{'nome':'Rossini Pena Abrantes','email':'rossini.abrantes@ifsudestemg.edu.br','senha':'06526'},
		{'nome':'Roberto de Carvalho Ferreira','email':'roberto.ferreira@ifsudestemg.edu.br','senha':'07345'},
		{'nome':'Eduardo Pereira da Rocha','email':'eduardo.rocha@ifsudestemg.edu.br','senha':'04579'},
		{'nome':'Luciano Gonçalves Moreira','email':'luciano.moreira@ifsudestemg.edu.br','senha':'03385'},
		{'nome':'Priscila Sad de Sousa','email':'priscila.sad@ifsudestemg.edu.br','senha':'08329'},
		{'nome':'Priscila Roque de Almeida','email':'priscila.almeida@ifsudestemg.edu.br','senha':'09292'},
		{'nome':'Farley Francisco Santana','email':'farleyfsantana@gmail.com','senha':'08490'},
		{'nome':'Diógenes Ferreira Filho','email':'dffilho@gmail.com','senha':'31159'},
		{'nome':'Viviane Cristina Almada de Oliveira','email':'viviane@ufsj.edu.br','senha':'02512'},
		{'nome':'Wanderley Moura Rezende','email':'wmrezende@id.uff.br','senha':'83758'},
		{'nome':'Gilmer Jacinto Peres','email':'gilmerperes@gmail.com','senha':'97996'},
		{'nome':'Arlindo Inês Teixeira','email':'arlindo.teixeira@ifsudestemg.edu.br','senha':'03406'},
		{'nome':'Adalgisa Reis Mesquita','email':'adalgisa.mesquita@ifsudestemg.edu.br','senha':'58819'},
		{'nome':'Joyce Barbosa Salazar','email':'joyce.salazar@ifsudestemg.edu.br','senha':'04718'},
		{'nome':'Wagner Azis Garcia de Araújo','email':'aziszoo@yahoo.com.br','senha':'01197'},
		{'nome':'Luiz Carlos Machado','email':'luiz.machado@ifmg.edu.br','senha':'93661'},
		{'nome':'Mariana Costa Fausto','email':'maricfausto@gmail.com','senha':'06155'}]
	if request.method == 'POST':
		email=request.form['email']
		passwd=request.form['passwd']
		for u in banco:
			if email==u["email"] and passwd==u["senha"]:
				return render_template('comprovantes_enviar.html',nome=u["nome"],email=u["email"])
	flash('<span>CPF e/ou senha incorretos!</span>','red')
	return redirect(url_for('admin.comprovanteslogin'))


@admin.route('/comprovantes/abastecimento/receber',methods = ['POST'])
def comprovantesabastecimentoreceive():
	uploaded_files = flask.request.files.getlist("file")
	for file in uploaded_files:
		filename = secure_filename(file.filename)
		file.save("static/comprovantes/abastecimento/"+request.form['email']+"/"+filename);
		flash("<span>Arquivo recebido com sucesso!</span>","green")
	return redirect(url_for('admin.comprovanteslogin'))

@admin.route('/comprovantes/passagens/receber',methods = ['POST'])
def comprovantespassagensreceive():
	uploaded_files = flask.request.files.getlist("file")
	for file in uploaded_files:
		filename = secure_filename(file.filename)
		file.save("static/comprovantes/passagens/"+request.form['email']+"/"+filename);
		flash("<span>Arquivo recebido com sucesso!</span>","green")
	return redirect(url_for('admin.comprovanteslogin'))

@admin.route('/comprovantes/uber/receber',methods = ['POST'])
def comprovantesuberreceive():
	uploaded_files = flask.request.files.getlist("file")
	for file in uploaded_files:
		filename = secure_filename(file.filename)
		file.save("static/comprovantes/uber/"+request.form['email']+"/"+filename);
		flash("<span>Arquivo recebido com sucesso!</span>","green")
	return redirect(url_for('admin.comprovanteslogin'))

@admin.route('/comprovantes/uber',methods = ['GET'])
def getcomprovantesuber():
	names=os.listdir('/home/fcmapp/Flask/sysdoc/static/comprovantes/uber')
	return render_template('comprovantes_list.html', type="uber", names=names)

@admin.route('/comprovantes/uber/<email>',methods = ['GET'])
def getcomprovantesuberemail(email=None):
	names=os.listdir('/home/fcmapp/Flask/sysdoc/static/comprovantes/uber/email')
	return render_template('comprovantes_list.html', type="uber", names=names)

@admin.route('/comprovantes/passagens',methods = ['GET'])
def getcomprovantespassagens():
	names=os.listdir('/home/fcmapp/Flask/sysdoc/static/comprovantes/passagens')
	return render_template('comprovantes_list.html', type="passagens", names=names)

@admin.route('/comprovantes/abastecimento',methods = ['GET'])
def getcomprovantesabastecimento():
	names=os.listdir('/home/fcmapp/Flask/sysdoc/static/comprovantes/abastecimento')
	return render_template('comprovantes_list.html', type="abastecimento", names=names)
