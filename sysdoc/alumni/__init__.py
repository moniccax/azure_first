
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
    logged=current_user
    return render_template('loginalumni.html', title='Login')

@alumni.route('/cadastro', methods = ['GET', 'POST'])
def cadastro():
    logged=current_user
    return render_template('ALUMNIcadastro.html', title='Cadastro')
