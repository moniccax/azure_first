from flask import Blueprint, render_template,request, flash, send_from_directory, abort
from utils import *


api = Blueprint('api', __name__,
                        template_folder='templates', static_folder='../static')
@api.route('/')
def index():
	return redirect(url_for('admin.index'))

@api.route('/serviceworker.js')
def static_from_root():
    return send_from_directory(api.static_folder, 'serviceworker.js')

@api.route('/offline',methods = ['GET'])
def offlineresponse():
	return render_template('offline.html', textError='Não há conexão com a internet!')

@api.route('/login', methods = ['GET', 'POST'])
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
					return jsonify(success=True,token=token,nome=logged.name)
				return jsonify(success=True,token=token,nome=logged.name)
		else:
			return jsonify(success=False)
	return jsonify(success=False)

@api.route('/islogged', methods = ['GET', 'POST'])
def islogged():
	token=request.get_json()['token']
	user=User.query.filter_by(token=token);
	if user:
		if is_logged(user,token):
			return jsonify(success=True);
	return jsonify(success=False);


def get_user(token):
	user=User.query.filter_by(token=token).first();
	if user:
		if is_logged(user,token):
			return user;
	abort(403)


@api.route('/updateProfilePic', methods=['GET', 'POST'])
def profile_update_profilepic():
	logged=get_user(request.form['token']);
	if logged:
		profilepicfile = request.files.get('file')
		if profilepicfile and (allowed_file(profilepicfile.filename, "png")):
			profilepic=logged.profilepicturepath;
			if profilepic is None or profilepic == "":
				newFileName=lcgProfilePictureNames()+".png";
				profilepicfile.save(PROFILEPIC_UPLOAD_FOLDER+"/"+newFileName)
				logged.profilepicturepath=PROFILEPIC_UPLOAD_FOLDER+"/"+newFileName
			else:
				profilepicfile.save(logged.profilepicturepath)
			db.session.commit()
			return jsonify(success=True);
	abort(403);

@api.route('/updatePassword', methods=['GET', 'POST'])
def profile_update_password():
	logged=get_user(request.get_json()['token']);
	if logged:
		if(hashlib.md5(request.get_json()['password'].encode('utf-8')).hexdigest()==logged.password):
			if(request.get_json()['newPassword']==request.get_json()['confirmNewPassword']):
				logged.password=hashlib.md5(request.get_json()['newPassword'].encode('utf-8')).hexdigest()
				db.session.commit()
				return jsonify(logged=True, success=True,message="Senha alterada com sucesso!");
			return jsonify(logged=True, success=False, message="As senhas não coincidem");
		return jsonify(logged=True, success=False, message="Senha incorreta");
	abort(403);


@api.route('/getProfileInfo', methods=['GET', 'POST'])
def getProfileInfo():
	logged=get_user(request.get_json()['token']);
	if logged:
		return jsonify(success=True,profilepicpath=logged.profilepicturepath, name=logged.name, cpf=logged.cpf, email=logged.email);
	return jsonify(success=False);


@api.route('/getPosts', methods=['GET', 'POST'])
def getPosts():
	logged=get_user(request.get_json()['token'])
	if logged:
		visible_posts=set()
		visible_contexts=set()
		posts_temp=Post_Context.query.filter()
		for relationship in posts_temp:
			permission=checkaccess(relationship,logged)
			if permission:
				visible_posts.add(relationship.post)
				visible_contexts.add(relationship.context)
		visible_posts_sorted=sorted(visible_posts, key=attrgetter('date'), reverse=True)
		visible_contexts_sorted=sorted(visible_contexts, key=attrgetter('name'))
		posts=[]
		for post in visible_posts_sorted:
			post_contexts=[]
			post_images=[]
			for ctx in post.contexts:
				post_contexts.append({"name":ctx.context.name, "color":ctx.context.color})
			for img in post.images:
				post_images.append(img.path)
			posts.append({"id":post.id, "author":post.author.name, "author_profilepic":post.author.getprofilepic(), "title":post.title, "text":post.text, "visibility":post.visibility, "date":post.date, "contexts":post_contexts, "images":post_images})
		contexts=[]
		for ctx in visible_contexts_sorted:
			contexts.append({"id":ctx.id, "name":ctx.name, "color":ctx.color});
		return jsonify(success=True, posts=posts, contexts=contexts)
	return jsonify(success=False)

@api.route('/getPost/<id>', methods=['GET', 'POST'])
def getPost(id=None):
	logged=get_user(request.get_json()['token'])
	if logged:
		post=Post.query.filter_by(id=id).first()
		editable=False
		for relationship in post.contexts:
			permission=checkaccess(relationship,logged);
			if permission and permission==2:
				editable=True
				break;
		for relationship in post.contexts:
			if checkaccess(relationship,logged):
				#post_comments=Post_Comment.query.filter_by(post_id=id).all()
				s=[]
				root_comments=Post_Comment.query.filter_by(post_id=id,parent_id=None).order_by(Post_Comment.date.desc());
				for comment in root_comments:
					s.append(print_comment_ionic(comment,logged));
				post_contexts=[]
				post_images=[]
				for ctx in post.contexts:
					post_contexts.append({"name":ctx.context.name, "color":ctx.context.color})
				for img in post.images:
					post_images.append(img.path)
				post={"id":post.id, "author":post.author.name, "author_profilepic":post.author.getprofilepic(), "title":post.title, "text":post.text, "visibility":post.visibility, "date":post.date.strftime("%d/%m/%Y %H:%M:%S"), "contexts":post_contexts, "images":post_images, "comments": s}
				return jsonify(success=True, post=post);
		return jsonify(success=False)
	abort(403);

@api.route('/getComment/<id>', methods=['GET', 'POST'])
def getComment(id=None):
	logged=get_user(request.get_json()['token'])
	if logged:
		comment=Post_Comment.query.filter_by(id=id).first()
		editable=False
		for relationship in comment.post.contexts:
			permission=checkaccess(relationship,logged);
			if permission and permission==2:
				editable=True
				break;
		for relationship in comment.post.contexts:
			if checkaccess(relationship,logged):
				#post_comments=Post_Comment.query.filter_by(post_id=id).all()
				comment={"id":comment.id, "author":comment.author.name, "author_profilepic":comment.author.getprofilepic(), "text":comment.text, "date":comment.date.strftime("%d/%m/%Y %H:%M:%S")}
				return jsonify(success=True, comment=comment);
		return jsonify(success=False)
	abort(403);


@api.route('/getVisibleContexts', methods=['GET', 'POST'])
def visibleContexts():
	logged=get_user(request.get_json()['token'])
	if logged:
		visible_contexts=set()
		posts_temp=Post_Context.query.filter()
		for relationship in posts_temp:
			permission=checkaccess(relationship,logged)
			if permission:
				visible_contexts.add(relationship.context)
		visible_contexts_sorted=sorted(visible_contexts, key=attrgetter('name'))
		contexts=[]
		for ctx in visible_contexts_sorted:
			contexts.append({"id":ctx.id, "name":ctx.name,"color":ctx.color});
		return jsonify(success=True, contexts=contexts)
	abort(403);

@api.route('/getUserContexts', methods=['GET', 'POST'])
def userContexts():
	logged=get_user(request.get_json()['token'])
	if logged:
		visible_contexts=set()
		user_contexts=[relationship.context for relationship in logged.contexts]
		for ctx in user_contexts:
			visible_contexts.add(ctx);
		visible_contexts_sorted=sorted(visible_contexts, key=attrgetter('name'))
		contexts=[]
		for ctx in visible_contexts_sorted:
			contexts.append({"id":ctx.id, "name":ctx.name,"color":ctx.color});
		return jsonify(success=True, contexts=contexts)
	abort(403);

@api.route('/getContext/<id>', methods=['GET', 'POST'])
def getContext(id=None):
	logged=get_user(request.get_json()['token'])
	if logged:
		ctx = Context.query.filter_by(id=id).first();
		users_context=User_Context.query.filter_by(context_id=id);
		members=[]
		for user_context in users_context:
			members.append({"id":user_context.user_id,"name":user_context.user.name,"administrator":user_context.administrator, "profilepicpath":user_context.user.getprofilepic()})
		context={"id":ctx.id, "name":ctx.name,"color":ctx.color,"members":members};
		return jsonify(success=True, context=context)
	abort(403);


@api.route('/createContext', methods = ['POST'])
def create_context():
	logged=get_user(request.get_json()['token'])
	name = request.get_json()['name']
	color = request.get_json()['ctx_color']
	moderated = request.get_json()['moderated']

	nameRegistered = Context.query.filter_by(name=name).first()
	colorRegistered = Context.query.filter_by(color=color).first()
	selected_members = request.get_json()["members"]
	if nameRegistered is not None:
		return jsonify(success=False, message='Já existe uma categoria com este nome.')
	if colorRegistered is not None:
		return jsonify(success=False, message='Já existe uma categoria com esta cor.')
	toadd=Context(name,color,moderated)
	db.session.add(toadd)
	db.session.commit()

	for member in selected_members:
		employeeUser = User.query.filter_by(id=member).first()
		context_to_add=User_Context();
		context_to_add.user=employeeUser;
		context_to_add.context=ctx;
		context_to_add.administrator=False;
		db.session.add(context_to_add)
	db.session.commit()

	return jsonify(success=True, message='Categoria cadastrada com sucesso!')


@api.route('/addPost', methods = ['GET', 'POST'])
def addPost():
	#logged=get_user(request.get_json()['token'])
	data=request.form['data'];
	d = json.loads(data)
	logged=get_user(d['token'])
	if logged:
		#post_title=request.get_json()['post_title']
		#post_text=request.get_json()['post_text']
		#post_visibility=request.get_json()['post_visibility']
		post_title=d['post_title']
		post_text=d['post_text']
		if d['post_visibility_1']:
			post_visibility=1
		if d['post_visibility_2']:
			post_visibility=2
		if d['post_visibility_3']:
			post_visibility=3
		toadd=Post(logged, post_title, post_text, post_visibility)
		db.session.add(toadd);
		#post_contexts=request.get_json()['post_contexts']
		uploaded_files = request.files.getlist('post_images[]')
		print(uploaded_files)
		for file in uploaded_files:
			if file and (allowed_file_array(file.filename, ["png","jpg","jpeg","gif","PNG","JPG","JPEG","GIF"])):
				ext=file.filename.split('.')[-1]
				newFileName=lcgPostImagesNames()+"."+ext;
				path=POST_IMAGES_UPLOAD_FOLDER+"/"+newFileName
				file.save(path)
				imgtoadd=Post_Image(path,toadd)
				db.session.add(imgtoadd);
		post_contexts=set()
		user_contexts=[relationship.context for relationship in logged.contexts]
		for ctx in user_contexts:
			if d['post_ctx_'+str(ctx.id)] is not None:
				post_contexts.add(ctx);
		for context in post_contexts:
			relationship=User_Context.query.filter_by(user=logged, context=context).first()
			if relationship is not None:
				toaddrelationship=Post_Context()
				toaddrelationship.post=toadd
				toaddrelationship.context=context
				if relationship.administrator==True or relationship.context.moderated==False:
					toaddrelationship.authorized=True;
				else:
					toaddrelationship.authorized=False;
				db.session.add(toaddrelationship)
		db.session.commit();
		return jsonify(success=True)
	abort(403)

@api.route('/addComment/<id>', methods = ['GET', 'POST'])
def addComment(id=None):
	logged=get_user(request.get_json()['token'])
	if id:
		post=Post.query.filter_by(id=id).first()
		text=request.get_json()['comment']
		if text is None or text == "":
			return jsonify(success=False, message="Comentário vazio!")
		else:
			toadd=Post_Comment(post, None, text, logged)
			db.session.add(toadd)
			db.session.commit()
			return jsonify(success=True, message="Mensagem registrada com sucesso!")
	abort(403);

@api.route('/deleteComment/<id>', methods = ['GET', 'POST'])
def deleteComment(id=None):
	logged=get_user(request.get_json()['token'])
	if id:
		comment=Post_Comment.query.filter_by(id=id).first()
		post=comment.post
		for relationship in post.contexts:
			permission=checkaccess(relationship,logged);
			if comment.author_id==logged.id or (permission and permission==2):
				db.session.delete(comment)
				db.session.commit()
				return jsonify(success=True, message="Comentário removido com sucesso!")
		return jsonify(success=False, message="Sem permissão para remover este comentário!")
	abort(403);

@api.route('/updateComment/<id>', methods = ['GET', 'POST'])
def editComment(id=None):
	logged=get_user(request.get_json()['token'])
	if id:
		post=Post.query.filter_by(id=id).first()
		text=request.get_json()['comment']
		if text is None or text == "":
			return jsonify(success=False, message="Comentário vazio!")
		else:
			toupdate=Post_Comment.query.filter_by(id=id).first();
			if toupdate.author == logged:
				toupdate.text=text;
				logged.date=datetime.datetime.now()
				db.session.commit()
			return jsonify(success=True, message="Mensagem registrada com sucesso!")
	abort(403);

@api.route('/answerComment/<id>', methods = ['GET', 'POST'])
def answerComment(id=None):
	logged=get_user(request.get_json()['token'])
	if id:
		parent=Post_Comment.query.filter_by(id=id).first()
		post=parent.post
		text=request.get_json()['comment']
		if text is None or text == "":
			return jsonify(success=False, message="Comentário vazio!")
		else:
			toadd=Post_Comment(post, parent, text, logged);
			db.session.add(toadd)
			db.session.commit()
			return jsonify(success=True, message="Mensagem registrada com sucesso!")
	abort(403)
