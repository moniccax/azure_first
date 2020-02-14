/* Cortar foto do perfil */

let crop_max_width = 400;
let crop_max_height = 400;
let jcrop_api;
let canvas;
let context;
let image;
let prefsize;

$("#file").change(function() {
	loadImage(this);
});

function loadImage(input) {
	if (input.files && input.files[0]) {
		let reader = new FileReader();
		canvas = null;
		reader.onload = function(e) {
			image = new Image();
			image.onload = validateImage;
			image.src = e.target.result;
		}
		reader.readAsDataURL(input.files[0]);
		$('#crop_p').removeClass("hide");
		$('#cropbutton').removeClass("hide");
	}
}

function dataURLtoBlob(dataURL) {
	let BASE64_MARKER = ';base64,';
	if (dataURL.indexOf(BASE64_MARKER) == -1) {
		let parts = dataURL.split(',');
		let contentType = parts[0].split(':')[1];
		let raw = decodeURIComponent(parts[1]);

		return new Blob([raw], {
			type: contentType
		});
	}
	let parts = dataURL.split(BASE64_MARKER);
	let contentType = parts[0].split(':')[1];
	let raw = window.atob(parts[1]);
	let rawLength = raw.length;
	let uInt8Array = new Uint8Array(rawLength);
	for (let i = 0; i < rawLength; ++i) {
		uInt8Array[i] = raw.charCodeAt(i);
	}

	return new Blob([uInt8Array], {
		type: contentType
	});
}

function validateImage() {
	if (canvas != null) {
		image = new Image();
		image.onload = validadeRestart;
		image.src = canvas.toDataURL('image/png');
	} else restartJcrop();
}

function validadeRestart() {
	if (jcrop_api != null) {
		jcrop_api.destroy();
	}
	$("#views").empty();
	$("#views").append("<canvas id=\"canvas\">");
	canvas = $("#canvas")[0];
	context = canvas.getContext("2d");
	canvas.width = image.width;
	canvas.height = image.height;
	context.drawImage(image, 0, 0);
	$("#canvas").Jcrop({
		aspectRatio: 4/4,
		allowMove: true,
		allowResize: true,
		onSelect: selectcanvas,
		onRelease: clearcanvas,
		boxWidth: crop_max_width,
		boxHeight: crop_max_height
	}, function() {
		jcrop_api = this;
	});
	clearcanvas();
}

function restartJcrop() {
	if (jcrop_api != null) {
		jcrop_api.destroy();
	}
	$("#views").empty();
	$("#views").append("<canvas id=\"canvas\">");
	canvas = $("#canvas")[0];
	context = canvas.getContext("2d");
	canvas.width = image.width;
	canvas.height = image.height;
	context.drawImage(image, 0, 0);
	let x1=$('canvas').width()/4;
	let y1=$('canvas').height()/4;
	let x2=(x1)+((2/4)*(Math.min($('canvas').width(),$('canvas').height())));
	let y2=(y1)+((2/4)*(Math.min($('canvas').width(),$('canvas').height())));
	$("#canvas").Jcrop({
		aspectRatio: 4/4,
		allowMove: true,
		allowResize: true,
		onSelect: selectcanvas,
		onRelease: clearcanvas,
		boxWidth: crop_max_width,
		boxHeight: crop_max_height,
		setSelect: [x1, y1, x2, y2]
	}, function() {
		jcrop_api = this;
	});
	clearcanvas();
}

function clearcanvas() {
	prefsize = {
		x: 0,
		y: 0,
		w: canvas.width,
		h: canvas.height,
	};
}

function selectcanvas(coords) {
	prefsize = {
		x: Math.round(coords.x),
		y: Math.round(coords.y),
		w: Math.round(coords.w),
		h: Math.round(coords.h)
	};
}

function applyCrop() {
	canvas.width = prefsize.w;
	canvas.height = prefsize.h;
	context.drawImage(image, prefsize.x, prefsize.y, prefsize.w, prefsize.h, 0, 0, canvas.width, canvas.height);
	validateImage();
	jcrop_api.release();
}

$("#cropbutton").click(function(e) {
	applyCrop();
});

$("#form").submit(function(e) {
	e.preventDefault();
	let profilepicname = $('#profilepicname').val();
	if (!profilepicname) {
		$('#pic_error').removeClass('hide');
	} else {
		formData = new FormData($("form[name='form']")[0]);
		let blob = dataURLtoBlob(canvas.toDataURL('images/png'));
		formData.append("cropped_image", blob, "blob.png");
		$.ajax({
			url: "https://admin.fundacaocefetminas.org.br/perfil/atualizar_foto_perfil",
			type: "POST",
			data: formData,
			contentType: false,
			cache: false,
			processData: false,
			success: function(data) {
				toastContent = $(data.message).add($('<button class="btn-flat toast-action"><i class="material-icons">clear</i></button>'));
				Materialize.toast(toastContent, undefined, data.color);
				if(data.success){
					$('.jcrop-holder').remove();
					$('#pic_error').addClass('hide');
					$('#crop_p').addClass("hide");
					$('#cropbutton').addClass("hide");
					$('#profilepicname').val("");
					$('#profilepic').attr("src", $('#profilepic').attr('src')+"?"+new Date().getTime());
				}
			},
			error: function(data) {
				Materialize.toast("Erro ao atualizar a imagem de perfil", undefined, "red");
			},
			complete: function(data) {}
		});
	}
});

/* Validação dos Formulários */

$("#form_profile_update").validate({
	rules : {
		email:{
			required:true,
			email:true
		}
	},
	messages:{
		email:{
			required:"Informe o E-mail.",
			email:"E-mail inválido!"
		}
	}
});

$("#form_sign_update").validate({
	rules : {
		signaturefilename:{
			required:true
		}
	},
	messages:{
		signaturefilename:{
			required:"É obrigatório anexar uma imagem."
		}
	}
});

$("#form_profile_changePass").validate({
	rules : {
		password:{
			required:true
		},
		newpassword:{
			required:true
		},
		newpassword2:{
			required:true,
			equalTo:"#newpassword"
		}
	},
	messages:{
		password:{
			required:"Digite sua senha atual."
		},
		newpassword:{
			required:"Defina uma nova senha."
		},
		newpassword2:{
			required:"Digite a nova senha novamente.",
			equalTo:"As senhas digitadas são diferentes."
		}
	}
});

/* Scroll */

$(function(){
	var hash = window.location.hash;
	$('html, body').animate({
		scrollTop: $(hash).offset().top-80
	}, 1000);
	$('#signatureimg').attr("src", $('#signatureimg').attr('src')+"?"+new Date().getTime());
	$('#profilepic').attr("src", $('#profilepic').attr('src')+"?"+new Date().getTime());
});
