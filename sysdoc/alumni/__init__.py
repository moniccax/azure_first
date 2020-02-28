
from flask import Blueprint, render_template,request, flash, url_for as flask_url_for, send_from_directory
from utils import *
from sqlalchemy import or_, and_
from operator import attrgetter
import hashlib


alumni = Blueprint('alumni', __name__,
                        template_folder='templates', static_folder='../static')

def url_for(endpoint, **values):
	url = flask_url_for(endpoint, **values);
	if(request.host=="app.fundacaocefetminas.org.br"):
		service=url.split('.')[0].split('/')[2];
		uri= url.split('.br')[1];
		url = "https://app.fundacaocefetminas.org.br/"+service+uri;
	return url;

@alumni.route('/', methods = ['GET', 'POST'])
def index():
    logged=current_user
    return render_template('homealumni.html', title='Home')

@alumni.route('/login', methods = ['GET', 'POST'])
def login():
    #logged=current_user
    if request.method == 'POST':
        alumni_cpf=request.form['cpf']
        passwd=request.form['password']
        if passwd!="":
            logged=Alumni.query.filter_by(cpf=alumni_cpf, password=hashlib.md5(passwd.encode('utf-8')))
        #if passwd=="Alumni#Login":
        #else
            #logged=Alumni.query.filter_by(cpf=alumni_cpf).first()
        if logged:
            login_user(logged) #,remember=form.remember_me.data
            db.session.commit()
            session.permanent = False
            if "remember_pass" in request.form:
                permanent_session=request.form['remember_pass']
                if permanent_session is not None and permanent_session:
                    session.permanent = True
                return redirect(url_for('alumni.index'))
#ADD MUDAR SENHA
        else:
            flash('<span>CPF e/ou senha incorretos!</span>','red')
    return render_template('loginalumni.html', title='Login')

@alumni.route('/cadastro', methods = ['GET', 'POST'])
def cadastro():
    #logged=current_user
    if request.method == 'POST':
        alumni_cpf=request.form['cpf']
        alumni_nome=request.form['nome']
        alumni_curso_id=request.form['curso_id']
        alumni_matricula=request.form['matricula']
        alumni_email=request.form['email']
        alumni_data_nascimento=request.form['data_nascimento']
        alumni_ano_ingresso=request.form['ano_ingresso']
        alumni_periodo_ingresso=request.form['periodo_ingresso']
        alumni_data_colacao=request.form['data_colacao']
        alumni_password=request.form['password']
        #alumni_cpfRegistered=Alumni.query.filter_by(cpf=cpf).first()
    return render_template('ALUMNIcadastro.html', title='Cadastro')
