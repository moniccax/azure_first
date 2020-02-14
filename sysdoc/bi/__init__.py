from flask import Blueprint, render_template, request, flash, url_for as flask_url_for, send_from_directory
from werkzeug.utils import secure_filename
from utils import *
import hashlib
import json

bi = Blueprint('bi', __name__,
                        template_folder='templates', static_folder='../static')

def url_for(endpoint, **values):
	url = flask_url_for(endpoint, **values);
	if(request.host=="app.fundacaocefetminas.org.br"):
		service=url.split('.')[0].split('/')[2];
		uri= url.split('.br')[1];
		url = "https://app.fundacaocefetminas.org.br/"+service+uri;
	return url;

@bi.route('/')
@login_required
def index():
	return redirect(url_for('admin.index'))
