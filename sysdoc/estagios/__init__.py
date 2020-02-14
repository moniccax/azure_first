
from flask import Blueprint, render_template,request, flash, url_for as flask_url_for, send_from_directory
from utils import *
from sqlalchemy import or_, and_
from operator import attrgetter
import hashlib


estagios = Blueprint('estagios', __name__,
                        template_folder='templates', static_folder='../static')

def url_for(endpoint, **values):
	url = flask_url_for(endpoint, **values);
	if(request.host=="app.fundacaocefetminas.org.br"):
		service=url.split('.')[0].split('/')[2];
		uri= url.split('.br')[1];
		url = "https://app.fundacaocefetminas.org.br/"+service+uri;
	return url;

@estagios.route('/', methods = ['GET', 'POST'])
def index():
    return render_template('indexestagios.html')

@estagios.route('/login', methods = ['GET', 'POST'])
def login():
    return render_template('/estagios/templates/login.html')
