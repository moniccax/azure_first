from flask import Blueprint, render_template,request, flash, send_from_directory
from utils import *
from datetime import timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import hashlib
import requests
import datetime
import time
import pickle
import os.path


mobile = Blueprint('mobile', __name__,
                        template_folder='templates', static_folder='../static')
@mobile.route('/')
def index():
	return redirect(url_for('admin.index'))

@mobile.route('/serviceworker.js')
def static_from_root():
    return send_from_directory(mobile.static_folder, 'serviceworker.js')

@mobile.route('/offline',methods = ['GET'])
def offlineresponse():
	return render_template('offline.html', textError='Não há conexão com a internet!')


@mobile.route('/denuncia_diretoria',methods=['POST'])
def denuncia_diretoria():
	# If modifying these scopes, delete the file token.pickle.
	SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

	# The ID and range of a sample spreadsheet.
	SPREADSHEET_ID = '1NgEcG2mlwVPT9pJ1TWUY6rh-vtB03sg4jij7hRRR3jU' #spreadsheet ID
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
	msg={};
	msg['Id']=request.form['id']
	msg['nome']=request.form['cont_nome']
	msg['email']=request.form['cont_email']
	msg['message']=request.form['cont_msg']
	msg['ip']=request.form['cont_ip']
	values=createRowDenuncia(msg) #create the line for the sheet
	body = {
		'values': values
	}
	#asks googlesheets API to append the line on sheet "Página1", simulating user entered values. (valueInputOption can be USER_ENTERED or RAW)
	result = service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range='denuncia', valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body=body).execute()
	return redirect('http://fundacaocefetminas.org.br/denuncia#sent-'+msg['ID'])

@mobile.route('/saveSorteio',methods=['POST'])
def sorteioidiomas():
	# If modifying these scopes, delete the file token.pickle.
	SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

	# The ID and range of a sample spreadsheet.
	SPREADSHEET_ID = '1csONqVI0CFdyCtLY9diKfHche5kkipcHtrCsA9GZ3sU' #spreadsheet ID
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
	user={};
	user['name']=request.form['whatsapp-nome']
	user['tel']=request.form['whatsapp-number']
	values=createRow(user) #create the line for the sheet
	body = {
		'values': values
	}
	#asks googlesheets API to append the line on sheet "Página1", simulating user entered values. (valueInputOption can be USER_ENTERED or RAW)
	result = service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range='Sorteio', valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body=body).execute()
	return redirect('http://fcmidiomas.com.br#sorteio')


@mobile.route('/formularioInteresse',methods=['POST'])
def formularioInteresse():
	# If modifying these scopes, delete the file token.pickle.
	SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

	# The ID and range of a sample spreadsheet.
	SPREADSHEET_ID = '1vAd9RDEKh56vE3zKuy0ajezEnkyE9tJEshoL9npGnZY' #spreadsheet ID
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
	user={};

	user['nome']=request.form['fi_name']
	user['email']=request.form['fi_email']
	user['tel']=request.form['fi_tel']
	user['idioma']=request.form['fi_idioma']
	user['experiencia']=request.form['fi_experiencia']
	values=createRowFormInteresse(user) #create the line for the sheet
	body = {
		'values': values
	}
	#asks googlesheets API to append the line on sheet "Página1", simulating user entered values. (valueInputOption can be USER_ENTERED or RAW)
	result = service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range='form', valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body=body).execute()
	return redirect('http://fcmidiomas.com.br#sucesso')
