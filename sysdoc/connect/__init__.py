#teste
from flask import Blueprint, render_template,request, flash, url_for as flask_url_for, send_from_directory
from utils import *
from sqlalchemy import or_, and_
from operator import attrgetter
import hashlib

connect = Blueprint('connect', __name__,
                        template_folder='templates', static_folder='../static')

def url_for(endpoint, **values):
	url = flask_url_for(endpoint, **values);
	if(request.host=="app.fundacaocefetminas.org.br"):
		service=url.split('.')[0].split('/')[2];
		uri= url.split('.br')[1];
		url = "https://app.fundacaocefetminas.org.br/"+service+uri;
	return url;

@connect.route('/')
def index():
	logged=current_user;
	user_admin=[]
	post_contexts=[]
	posts=set()
	editable_posts=set()
	visible_contexts=set();
	posts_temp=Post_Context.query.filter()
	for relationship in posts_temp:
		permission=checkaccess(relationship,logged);
		if permission:
			posts.add(relationship.post)
			visible_contexts.add(relationship.context);
			if permission==2:
				editable_posts.add(relationship.post.id)
	if logged.is_authenticated:
		post_contexts=logged.contexts;
		output=getNotifications(logged)
	posts=sorted(posts, key=attrgetter('date'), reverse=True)
	visible_contexts_sorted=sorted(visible_contexts, key=attrgetter('name'))
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'connect', render_template('posts.html', posts=posts, editable_posts=editable_posts, user=logged,categories=visible_contexts_sorted,user_admin=user_admin,post_categories=post_contexts, maintenance=maintenance, gmt_timezone=GMT_TIMEZONE, timezone=TIMEZONE))

@connect.route('/ctx', methods = ['GET', 'POST'])
def filtercontext():
	logged=current_user;
	user_admin=[]
	post_contexts=[]
	posts=set()
	editable_posts=set()
	visible_contexts=set()
	selected_contexts_return=set()
	posts_temp=Post_Context.query.filter()
	selected_contexts = request.form.getlist("selected_contexts")
	if len(selected_contexts) == 0:
		return redirect(url_for('connect.index'))
	for ctx in selected_contexts:
		context=Context.query.filter_by(id=ctx).first();
		if context is not None:
			posts_temp=Post_Context.query.filter()
			selected_contexts_return.add(context.id)
		for relationship in posts_temp:
			permission=checkaccess(relationship,logged)
			if permission:
				if relationship.context_id == context.id:
					posts.add(relationship.post)
					if permission==2:
						editable_posts.add(relationship.post.id)
				visible_contexts.add(relationship.context)
	if logged.is_authenticated:
		post_contexts=logged.contexts;
		output=getNotifications(logged)
	posts=sorted(posts, key=attrgetter('date'), reverse=True)
	visible_contexts_sorted=sorted(visible_contexts, key=attrgetter('name'))
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'connect', render_template('posts.html', posts=posts, editable_posts=editable_posts, user=logged,categories=visible_contexts_sorted,user_admin=user_admin,post_categories=post_contexts, selected_ctx=selected_contexts_return, maintenance=maintenance, gmt_timezone=GMT_TIMEZONE, timezone=TIMEZONE))


@connect.route('/usuario/<id>')
def filterUser(id=None):
	logged=current_user;
	user_admin=[]
	post_contexts=[]
	user_posts=Post.query.filter_by(author_id=id).all()
	author=User.query.filter_by(id=id).first()
	author_name=author.name
	posts=set()
	editable_posts=set()
	visible_contexts=set();
	posts_temp=Post_Context.query.filter()
	for relationship in posts_temp:
		permission=checkaccess(relationship,logged)
		if permission:
			for up in user_posts:
				if relationship.post_id == up.id:
					posts.add(relationship.post)
					if permission==2:
						editable_posts.add(relationship.post.id)
				visible_contexts.add(relationship.context)
	if logged.is_authenticated:
		post_contexts=logged.contexts;
		output=getNotifications(logged)
	posts=sorted(posts, key=attrgetter('date'), reverse=True)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'connect', render_template('user_posts.html', posts=posts, editable_posts=editable_posts, user=logged, author_name=author_name, categories=visible_contexts,user_admin=user_admin,post_categories=post_contexts, maintenance=maintenance, gmt_timezone=GMT_TIMEZONE, timezone=TIMEZONE))


@connect.route('/desbloquear/')
def filterLockedPosts():
	logged=current_user;
	posts=set()
	visible_contexts=set()
	editable_posts=set()
	user_context=User_Context.query.filter_by(user_id=logged.id, administrator=True)
	posts_temp=Post_Context.query.filter()
	for relationship in posts_temp:
		permission=checkaccess(relationship,logged)
		if permission:
			for uc in user_context:
				if relationship.context_id == uc.context_id and not relationship.authorized:
					posts.add(relationship.post)
					if permission==2:
						editable_posts.add(relationship.post.id)
				visible_contexts.add(uc.context)
	if logged.is_authenticated:
		post_contexts=logged.contexts;
		output=getNotifications(logged)
	posts=sorted(posts, key=attrgetter('date'), reverse=True)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	return verifyMaintenance(logged, 'connect', render_template('posts.html', posts=posts, editable_posts=editable_posts, user=logged, categories=visible_contexts, post_categories=post_contexts, maintenance=maintenance, gmt_timezone=GMT_TIMEZONE, timezone=TIMEZONE))


@connect.route('/desbloquear_post/<pid>/<cid>')
def unlockPost(pid=None, cid=None):
	logged=current_user
	post_context=Post_Context.query.filter_by(post_id=pid, context_id=cid).first()
	context_admin=User_Context.query.filter_by(user_id=logged.id, context_id=cid, administrator=True).first()
	if context_admin:
		post_context.authorized=True
		db.session.commit()
		return jsonify(success=True, message='<span>Post desbloqueado com sucesso!</span>',color='green')
	return jsonify(success=False, message='<span>Você não possui permissão para desbloquear o post.</span>',color='red')


@connect.route('/bloquear_post/<pid>/<cid>')
def blockPost(pid=None, cid=None):
	logged=current_user
	post_context=Post_Context.query.filter_by(post_id=pid, context_id=cid).first()
	context_admin=User_Context.query.filter_by(user_id=logged.id, context_id=cid, administrator=True).first()
	if context_admin:
		post_context.authorized=False
		db.session.commit()
		return jsonify(success=True, message='<span>Post bloqueado com sucesso!</span>',color='green')
	return jsonify(success=False, message='<span>Você não possui permissão para bloaquear o post.</span>',color='red')


@connect.route('/post/<id>', methods = ['GET'])
def post(id=None):
	logged=current_user
	post=Post.query.filter_by(id=id).first()
	post_contexts=None
	editable_posts=None
	if logged.is_authenticated:
		post_contexts=logged.contexts
		editable_posts=set()
		posts_temp=Post_Context.query.filter()
		for relationship in posts_temp:
			permission=checkaccess(relationship,logged);
			if permission:
				if permission==2:
					editable_posts.add(relationship.post.id)
	for relationship in post.contexts:
		if checkaccess(relationship,logged):
			post_comments=Post_Comment.query.filter_by(post_id=id).all()
			maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
			root_comments=Post_Comment.query.filter_by(post_id=id,parent_id=None).order_by(Post_Comment.date.desc());
			s = ""
			for comment in root_comments:
				s+=print_comment(comment,logged);
			return verifyMaintenance(logged, 'connect', render_template('post.html', user=logged, post=post, s=s, editable_posts=editable_posts, post_categories=post_contexts, post_comments=post_comments, maintenance=maintenance, gmt_timezone=GMT_TIMEZONE, timezone=TIMEZONE))
	return redirect(url_for('connect.index'))

@connect.route('/post/criar', methods = ['GET', 'POST'])
@login_required
def create_post():
	logged=current_user
	title=request.form['title']
	body=request.form['body']
	body = "<br />".join(body.split("\n"))
	contexts_selected=set();
	contexts=Context.query
	for context in contexts:
		selected=request.form.get('ap_cb_category_'+str(context.id))
		if selected is not None and selected==str(context.id):
			contexts_selected.add(context)
	visibility=request.form['visibility']
	uploaded_files = request.files.getlist('uploadImage')
	toadd=Post(logged,title,body,visibility);
	for file in uploaded_files:
		if file and (allowed_file_array(file.filename, ["png","jpg","jpeg","gif","PNG","JPG","JPEG","GIF"])):
			ext=file.filename.split('.')[-1]
			newFileName=lcgPostImagesNames()+"."+ext;
			path=POST_IMAGES_UPLOAD_FOLDER+"/"+newFileName
			file.save(path)
			imgtoadd=Post_Image(path,toadd)
			db.session.add(imgtoadd);
	for context in contexts_selected:
		relationship=User_Context.query.filter_by(user=logged, context=context).first();
		if relationship is not None:
			toaddrelationship=Post_Context();
			toaddrelationship.post=toadd;
			toaddrelationship.context=context;
			if relationship.administrator==True or relationship.context.moderated==False:
				toaddrelationship.authorized=True;
				flash('<span>Post adicionado com sucesso na categoria '+context.name+'!</span>','green')
			else:
				toaddrelationship.authorized=False;
				flash('<span>Post adicionado com sucesso à categoria '+context.name+'! Aguarde autorização do administrador</span>','green')
			db.session.add(toadd);
			db.session.add(toaddrelationship)
		else:
			flash('<span>Você não tem permissão para postar na categoria '+context.name+'!</span>','red')
	db.session.commit();
	return redirect(url_for('connect.index'))


@connect.route('/post/editar/<id>', methods = ['GET','POST'])
@login_required
def edit_post(id=None):
	logged=current_user
	post=Post.query.filter_by(id=id).first();
	if post:
		if logged==post.author or logged.category<=1000:

			# Adicionar novas imagens ao post
			images = request.files.getlist('uploadImage_'+str(id))
			for img in images:
				if img and (allowed_file_array(img.filename, ["png","jpg","jpeg","gif","PNG","JPG","JPEG","GIF"])):
					ext=img.filename.split('.')[-1]
					newFileName=lcgPostImagesNames()+"."+ext;
					path=POST_IMAGES_UPLOAD_FOLDER+"/"+newFileName
					img.save(path)
					imgtoadd=Post_Image(path,post)
					db.session.add(imgtoadd)

			# Titulo
			title=request.form['title_'+str(id)]
			post.title=title

			# Texto
			body=request.form['body_'+str(id)]
			post.text=body

			# Contextos
			# Antigos
			contexts_old=set()
			post_contexts = Post_Context.query.filter_by(post=post)
			for pc in post_contexts:
				contexts_old.add(pc)
			# Novos
			contexts_new=set()
			contexts=Context.query
			for context in contexts:
				selected=request.form.get('cb_category_'+str(context.id)+'_'+str(post.id))
				if selected is not None and selected==str(context.id):
					contexts_new.add(context)
			for co in contexts_old:
				if co not in contexts_new:
					ctx = Context.query.filter_by(id=co.context.id).first()
					Post_Context.query.filter_by(context=ctx, post=post).delete()
			for cn in contexts_new:
				if cn not in contexts_old:
					relationship=User_Context.query.filter_by(user=logged, context=cn).first();
					if relationship is not None:
						toaddrelationship=Post_Context();
						toaddrelationship.post=post;
						toaddrelationship.context=cn;
						if relationship.administrator==True or relationship.context.moderated==False:
							toaddrelationship.authorized=True;
						else:
							toaddrelationship.authorized=False;
						db.session.add(toaddrelationship)

			# Visibilidade
			visibility=request.form['visibility_'+str(post.id)]
			post.visibility=visibility

			db.session.commit()
			flash('<span>Edição efetuada com sucesso!</span>','green')
	return redirect(url_for('connect.index'))


@connect.route('/post/remover_imagem/<id>', methods = ['GET','POST'])
@login_required
def remove_img_post(id=None):
	logged=current_user
	post_img=Post_Image.query.filter_by(id=id).first()
	post_id=post_img.post.id
	post=Post.query.filter_by(id=post_id).first()
	if post_img:
		if logged==post.author or logged.category<=1000:
			try:
				os.remove(post_img.path)
			except OSError as e:
				print(e.errno)
			Post_Image.query.filter_by(id=id).delete()
			db.session.commit()
			return jsonify(success=True, message='<span>Imagem removida com sucesso!</span>',color='green')
		return jsonify(success=False, message='<span>Você não possui permissão para remover imagens do post.</span>',color='red')
	return redirect(url_for('connect.index'))


@connect.route('/post/remover/<id>', methods = ['GET'])
@login_required
def delete_post(id=None):
	logged=current_user
	post=Post.query.filter_by(id=id).first();
	if post:
		if logged==post.author or logged.category<=1000:
			post_files=Post_Image.query.filter_by(post=post);
			for post_file in post_files:
				try:
					os.remove(post_file.path);
					break;
				except OSError as e:
					print(e.errno)
			post_files.delete();
			Post_Context.query.filter_by(post=post).delete();
			Post_Comment.query.filter_by(post=post).delete();
			Post.query.filter_by(id=id).delete();
			db.session.commit();
			flash('<span>Post removido com sucesso!</span>','green');
			return redirect(url_for('connect.index'))
		post_contexts=Post_Context.query.filter_by(post=post);
		user_admin_relationship=User_Context.query.filter_by(user=logged,administrator=True)
		user_admin=[admin_context.context for admin_context in user_admin_relationship]
		for post_context in post_contexts:
			if post_context in user_admin:
				Post_Context.query.filter_by(post=post, context=post_context).delete();
		if not Post_Context.query.filter_by(post=post).first():
			post_files=Post_Image.query.filter_by(post=post);
			for post_file in post_files:
				try:
					os.remove(post_file.path);
					break;
				except OSError as e:
					print(e.errno)
			post_files.delete();
			post=Post.query.filter_by(id=id).delete();
		db.session.commit();
		flash('<span>Post removido das categorias que você administra com sucesso!</span>','green');
		return redirect(url_for('connect.index'))
	flash('<span>Ocorreu um erro ao remover o post!</span>','red');
	return redirect(url_for('connect.index'))


@connect.route('/post/comentar_existente/<id>', methods = ['POST'])
@login_required
def comment_post(id=None):
	logged=current_user
	if id:
		parent=Post_Comment.query.filter_by(id=id).first()
		post=parent.post
		text=request.form['txt_comment_'+str(id)]
		if text is None or text == "":
			flash('<span>Escreva um comentário!</span>','red')
		else:
			toadd=Post_Comment(post, parent, text, logged)
			db.session.add(toadd)
			db.session.commit()
			flash('<span>Comentário registrado com sucesso!</span>','green')
	else:
		flash('<span>Você precisa estar logado para comentar!</span>','red')
	return redirect(url_for('connect.post', id=post.id))


@connect.route('/post/comentar/<id>', methods = ['POST'])
@login_required
def new_comment(id=None):
	logged=current_user
	if id:
		post=Post.query.filter_by(id=id).first()
		text=request.form['new_comment']
		if text is None or text == "":
			flash('<span>Escreva um comentário!</span>','red')
		else:
			toadd=Post_Comment(post, None, text, logged)
			db.session.add(toadd)
			db.session.commit()
			flash('<span>Comentário registrado com sucesso!</span>','green')
	else:
		flash('<span>Você precisa estar logado para comentar!</span>','red')
	return redirect(url_for('connect.post', id=id))


@connect.route('/post/editar_comentario/<id>', methods = ['POST'])
@login_required
def edit_comment(id=None):
	logged=current_user
	if id:
		post_comment=Post_Comment.query.filter_by(id=id).first()
		text=request.form['comment_'+str(id)]
		if text is None or text == "":
			flash('<span>Escreva um comentário!</span>','red')
		else:
			post_comment.text=text
			db.session.commit()
			flash('<span>Edição efetuada com sucesso!</span>','green')
	else:
		flash('<span>Você precisa estar logado para comentar!</span>','red')
	return redirect(url_for('connect.post', id=post_comment.post.id))


@connect.route('/post/excluir_comentario/<id>', methods = ['GET','POST'])
@login_required
def delete_comment(id=None):
	logged=current_user
	if id:
		post_comment=Post_Comment.query.filter_by(id=id).first()
		post_id = post_comment.post.id
		child=Post_Comment.query.filter_by(post_id=post_id, parent=post_comment).first()
		if child:
			flash('<span>Você não pode excluir esse comentário!</span>','red')
		else:
			Post_Comment.query.filter_by(id=id).delete()
			db.session.commit()
			flash('<span>Exclusão efetuada com sucesso!</span>','green')
	return redirect(url_for('connect.post', id=post_id))


@connect.route('/categorias', methods = ['GET', 'POST'])
@login_required
@requires_roles(2000)
def categories_list():
	logged=current_user
	output=getNotifications(logged)
	maintenance=Systemsettings.query.filter_by(key="maintenance").first().value
	if logged.category<=1000:
		contexts=Context.query.filter_by();
	else:
		admin_contexts=User_Context.query.filter_by(user=logged, administrator=True);
		contexts=list(admin_context.context for admin_context in admin_contexts)
	employeeUsers=User.query.filter(User.category<3000)
	employeeUsers_sorted=sorted(employeeUsers, key=lambda user: user.name)
	return verifyMaintenance(logged, 'connect', render_template('categories.html', user=logged, notifications=output,categories=contexts, employeeUsers=employeeUsers, employeeUsers_sorted=employeeUsers_sorted, maintenance=maintenance))
	return redirect('/')

@connect.route('/categorias/cadastrar', methods = ['GET', 'POST'])
@login_required
@requires_roles(2000)
def create_category():
	logged=current_user
	name = request.form['name']
	color = request.form['ctx_color']
	moderated_bool = 0
	if "moderated" in request.form:
		moderated = request.form['moderated']
		if moderated:
			moderated_bool = 1
	nameRegistered = Context.query.filter_by(name=name).first()
	colorRegistered = Context.query.filter_by(color=color).first()
	selected_members = request.form.getlist("members")
	if name == "":
		flash('<span>É obrigatório definir o nome da nova categoria.</span>','red')
	elif nameRegistered is not None:
		flash('<span>Já existe uma categoria com este nome.</span>','red')
	elif colorRegistered is not None:
		flash('<span>Já existe uma categoria com esta cor.</span>','red')
	else:
		toadd=Context(name,color,moderated_bool)
		db.session.add(toadd)
		db.session.commit()

		ctx = Context.query.filter_by(name=name).first();

		for member in selected_members:
			employeeUser = User.query.filter_by(id=member).first()
			context_to_add=User_Context();
			context_to_add.user=employeeUser;
			context_to_add.context=ctx;
			context_to_add.administrator=False;
			db.session.add(context_to_add)
		db.session.commit()

		flash('<span>Categoria cadastrada com sucesso!</span>','green')
	return redirect(url_for('connect.categories_list'))


@connect.route('/categorias/remover/<id>', methods = ['GET', 'POST'])
@login_required
@requires_roles(2000)
def remove_category(id=None):
	logged=current_user
	destination_id=request.form['category_value_'+id]
	toRemove = Context.query.filter_by(id=id).first()
	destination_cat=Context.query.filter_by(id=destination_id).first()
	if toRemove.users is not None:
		User_Context_tomove=User_Context.query.filter_by(context=toRemove);
		if destination_cat is not None:
			for relation in User_Context_tomove:
				relation.context=destination_cat;
		else:
			User_Context.query.filter_by(context=toRemove).delete();
			db.session.commit();
	if toRemove.posts is not None:
		if destination_cat is not None:
			for post in toRemove.posts:
				post.context=destination_cat;
		else:
			posts_contexts=Post_Context.query.filter_by(context_id=id);
			posts=[p_c.post for p_c in posts_contexts];
			for post in posts:
				if len(post.contexts)==1:
					Post_Context.query.filter_by(context_id=id, post_id=post.id).delete();
					Post_Image.query.filter(Post_Image.post.has(Post.context_id==id)).delete(synchronize_session=False)
					Post_Comment.query.filter(Post_Comment.post.has(Post.context_id==id)).delete(synchronize_session=False)
					db.session.delete(post);
				else:
					Post_Context.query.filter_by(context_id=id, post_id=post.id).delete();
			db.session.commit()
	db.session.delete(toRemove)
	db.session.commit()
	flash('<span>Categoria removida com sucesso!</span>','green')
	return redirect(url_for('connect.categories_list'))

@connect.route('/offline',methods = ['GET'])
def offlineresponse():
	return render_template('offline.html', textError='Não há conexão com a internet!')
