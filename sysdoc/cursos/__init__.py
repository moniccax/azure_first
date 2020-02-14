from flask import Blueprint, render_template,request, flash, send_from_directory
from utils import *


cursos = Blueprint('cursos', __name__,
                        template_folder='templates', static_folder='../static')
@cursos.route('/')
def index():
	return redirect(url_for('cursos.cursoscadastro'))

@cursos.route('/serviceworker.js')
def static_from_root():
    return send_from_directory(cursos.static_folder, 'serviceworker.js')

@cursos.route('/offline',methods = ['GET'])
def offlineresponse():
	return render_template('offline.html', textError='Não há conexão com a internet!')

#===================================================================================================
#CURSOS=============================================================================================
#===================================================================================================

@cursos.route('/cursos',methods = ['GET'])
def cursoscod():
	return render_template('cursos.html')

@cursos.route('/cursos/cadastro',methods = ['GET'])
def cursoscadastro():
	return render_template('cursoscadastro.html')


@cursos.route('/cursos/enviar_email', methods = ['GET', 'POST'])
def send_email_courses():
	# 1 - Solicitante(s)
	nome=request.form['nome']
	campus=request.form['campus']
	dept=request.form['dept']
	telefone=request.form['telefone']
	email=request.form['email']
	equipes=request.form['equipes']
	equipes="<br />".join(equipes.split("\n"))
	nome_ext_list=request.form.getlist('nome_ext[]')
	inst_ext_list=request.form.getlist('inst_ext[]')
	telefone_ext_list=request.form.getlist('telefone_ext[]')
	email_ext_list=request.form.getlist('email_ext[]')
	# 2 - Dados do Curso
	titulo_curso=request.form['titulo_curso']
	area_conc=request.form['area_conc']
	area_conc="<br />".join(area_conc.split("\n"))
	apresentacao_curso=request.form['apresentacao_curso']
	apresentacao_curso="<br />".join(apresentacao_curso.split("\n"))
	corpo_docente=request.form['corpo_docente']
	corpo_docente="<br />".join(corpo_docente.split("\n"))
	modalidade_curso=request.form['modalidade_curso']
	carga_horaria=request.form['carga_horaria']
	sala_lab=request.form['sala_lab']
	organizacao_curso=request.form['organizacao_curso']
	if 'outros_text' in request.form:
		outros=request.form['outros_text']
	# 3 - Ofertar
	coffe_break=request.form['coffe_break']
	apostila=request.form['apostila']
	certificado=request.form['certificado']
	ofertar_outros=request.form['ofertar_outros']
	ofertar_outros="<br />".join(ofertar_outros.split("\n"))
	# 4 - Valores
	valor_hora_aula=request.form['valor_hora_aula']
	valor_coord=request.form['valor_coord']
	valor_aluno=request.form['valor_aluno']
	# 5 - Público Alvo
	publico_alvo=request.form['publico_alvo']
	publico_alvo="<br />".join(publico_alvo.split("\n"))
	# 6 - Canais de Divulgação do Evento
	canais_divulgacao=request.form['canais_divulgacao']
	canais_divulgacao="<br />".join(canais_divulgacao.split("\n"))
	# 6 - Observações
	observacoes=request.form['observacoes']
	observacoes="<br />".join(observacoes.split("\n"))

	subject = "Proposta Cursos Livres"
	msg = '''
		<p><b>1 - SOLICITANTE(S):</b></p>
		<p><b>Nome: </b>'''+nome+'''</p>
		<p><b>Identificação da origem do solicitante:</b></p>
		<p><b>Campus: </b>'''+campus+'''</p>
		<p><b>Departamento/Coordenação: </b>'''+dept+'''</p>
		<p><b>Telefone: </b>'''+telefone+'''</p>
		<p><b>E-mail: </b>'''+email+'''</p>
		<p><b>Equipes Participantes:</b><br>
		'''+equipes+'''</p>'''


	if nome_ext_list[0] != "":
		for index in range(0, len(nome_ext_list)):
			msg +='''
			<p><b>Instituições externas envolvidas (caso existam) e responsáveis:</b></p>
			<p>
			<ul>
			<li><b>Nome: </b>'''+nome_ext_list[index]+'''</li>
			<li><b>Instituição: </b>'''+inst_ext_list[index]+'''</li>
			<li><b>Telefone: </b>'''+telefone_ext_list[index]+'''</li>
			<li><b>E-mail: </b>'''+email_ext_list[index]+'''</li>
			</ul>
			</p>'''

	msg+='''
		<hr>
		<p><b>2 - DADOS DO CURSO:</b></p>
		<p><b>Título: </b>'''+titulo_curso+'''</p>
		<p><b>Área de Concentração: </b><br>
		'''+area_conc+'''</p>
		<p><b>Apresentação do Curso: </b><br>
		'''+apresentacao_curso+'''</p>
		<p><b>Corpo Docente: </b><br>
		'''+corpo_docente+'''</p>
		<p><b>Modalidade: </b>'''+modalidade_curso+'''</p>
		<p><b>Carga Horária: </b>'''+carga_horaria+'''</p>
		<p><b>Sala/Laboratório: </b>'''+sala_lab+'''</p>
		<p><b>Organização: </b>'''+organizacao_curso

	if 'outros_text' in request.form:
		msg+=''' - '''+outros

	msg+='''
		</p>
		<hr>
		<p><b>3 - OFERTAR</b></p>
		<p><b>Coffe Break: </b>'''+coffe_break+'''</p>
		<p><b>Apostila: </b>'''+apostila+'''</p>
		<p><b>Certificado: </b>'''+certificado+'''</p>'''

	if ofertar_outros != "":
		msg+='''	
		<p><b>Outros (equipamentos, materiais etc.): </b><br>
		'''+ofertar_outros+'''</p>'''

	msg+='''
		<hr>
		<p><b>4 - VALORES:</b></p>
		<p><b>Valor hora aula ministrada: </b>'''+valor_hora_aula+'''</p>'''

	if valor_coord != "":
		msg+='''
		<p><b>Valor Coordenação (se houver): </b>'''+valor_coord+'''</p>'''

	msg+='''
		<p><b>Valor sugerido para custo do curso, por aluno: </b>'''+valor_aluno+'''</p>

		<hr>
		<p><b>5 - PÚBLICO ÁLVO:</b></p>
		<p>'''+publico_alvo+'''</p>

		<hr>
		<p><b>6 - CANAIS DE DIVULGAÇÃO DO EVENTO:</b></p>
		<p>'''+canais_divulgacao+'''</p>'''

	if observacoes != "":
		msg+='''
		<hr>
		<p><b>OBSERVAÇÕES:</b></p>
		<p>'''+observacoes+'''</p>'''

	send_email(subject, "fcm_documentos@fundacaocefetminas.org.br", "angela@fundacaocefetminas.org.br", "", msg)
	flash('<span>E-mail enviado com sucesso!</span>','green')
	return redirect(url_for('cursos.cursoscadastro'))
