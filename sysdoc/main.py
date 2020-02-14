# -*- coding: latin-1 -*-
from flask import request, jsonify, render_template, flash, url_for, Blueprint
from docx import Document as docxDocument
from datetime import timedelta
from subprocess import call
from utils import *
import os
import io
import zipfile
import sys
import hashlib
import random
import string
import flask


#@application.before_request,
#def make_session_permanent():
#    session.permanent = True
#    application.permanent_session_lifetime = timedelta(minutes=15)


from admin import admin
application.register_blueprint(admin, subdomain='admin')

from docs import docs
application.register_blueprint(docs, subdomain='documentos')

from connect import connect
application.register_blueprint(connect, subdomain='conecta')

from cursos import cursos
application.register_blueprint(cursos, subdomain='cursos')

from api import api
application.register_blueprint(api, subdomain='api')

from app import mobile
application.register_blueprint(mobile, subdomain='app')

from alumni import alumni
application.register_blueprint(alumni, subdomain='alumni')

from estagios import estagios
application.register_blueprint(estagios, subdomain='estagios')

from bi import bi
application.register_blueprint(bi, subdomain='bi')


application.register_blueprint(admin,subdomain='app', url_prefix='/admin')
application.register_blueprint(docs,subdomain='app', url_prefix='/documentos')
application.register_blueprint(connect,subdomain='app', url_prefix='/conecta')
application.register_blueprint(cursos,subdomain='app', url_prefix='/cursos')
application.register_blueprint(alumni,subdomain='app', url_prefix='/alumni')
application.register_blueprint(estagios,subdomain='app', url_prefix='/estagios')
application.register_blueprint(bi,subdomain='app', url_prefix='/bi')


@application.route('/')
def index():
	return redirect(url_for('admin.index'))

# PÁGINAS DE ERRO

@application.errorhandler(404)
def page_error404(e):
	return redirect("/")
    #return render_template('erro.html', textError='Página não encontrada!'), 404


@application.errorhandler(500)
def page_error500(e):
    return render_template('erro.html', textError='O sistema se comportou de forma inesperada!'), 500


@application.errorhandler(403)
def page_error403(e):
    return render_template('erro.html', textError='Você não possui permissão para acessar esta página!'), 403

@application.after_request
def add_headers(response):
	response.headers.add('Access-Control-Allow-Credentials', 'true')
	response.headers.add('Vary', 'Origin')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
	return response
