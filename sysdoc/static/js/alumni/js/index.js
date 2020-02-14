/*$(window).on('load', function () {
	if(window.location.href.indexOf("sorteio") == -1) {
		setTimeout(function() {
			$('#onleavepage').modal('open');
		}, 20000);
	}

	if(window.location.href.indexOf("sucesso") != -1) {
		$('#email_enviado').modal('open');
	}

	if(window.location.href.indexOf("sorteio") != -1) {
		$('#whatsapp_enviado').modal('open');
	}
});*/

$(document).ready(function() {

	if( navigator.userAgent.match(/Android/i)
		|| navigator.userAgent.match(/webOS/i)
		|| navigator.userAgent.match(/iPhone/i)
		|| navigator.userAgent.match(/iPad/i)
		|| navigator.userAgent.match(/iPod/i)
		|| navigator.userAgent.match(/BlackBerry/i)
		|| navigator.userAgent.match(/Windows Phone/i)
		){
		$('.portfolio_slider').slick({
			slidesToShow: 1,
			slidesToScroll: 1,
			arrows: true,
			prevArrow: '<button type="button" class="slick-prev"><i class="fas fa-chevron-left"></i></button>',
			nextArrow:' <button type="button" class="slick-next"><i class="fas fa-chevron-right"></i></button>'
		});
	} else {
		$('.portfolio_slider').slick({
			slidesToShow: 3,
			slidesToScroll: 1,
			arrows: true,
			prevArrow: '<button type="button" class="slick-prev"><i class="fas fa-chevron-left"></i></button>',
			nextArrow:' <button type="button" class="slick-next"><i class="fas fa-chevron-right"></i></button>'
		});
	}

});

$(window).scroll(function(){
	if(window.scrollY>0){
		$("nav").css('background','rgba(12,108,212,0.50)');
	}else{
		$("nav").css('background','transparent');
	}
});

$('.scrooldown a').bind('click', function () {
	$('html , body').stop().animate({
		scrollTop: $($(this).attr('href')).offset().top - 60
	}, 1500, 'easeInOutExpo');
	event.preventDefault();
});

/* Máscara para telefone */

function fMasc(objeto,mascara) {
	obj=objeto
	masc=mascara
	setTimeout("fMascEx()",1)
}
function fMascEx() {
	obj.value=masc(obj.value)
}

function mTel(tel) {
	tel=tel.replace(/\D/g,"")
	tel=tel.replace(/^(\d)/,"($1")
	tel=tel.replace(/(.{3})(\d)/,"$1)$2")
	if(tel.length == 9) {
		tel=tel.replace(/(.{1})$/,"-$1")
	} else if (tel.length == 10) {
		tel=tel.replace(/(.{2})$/,"-$1")
	} else if (tel.length == 11) {
		tel=tel.replace(/(.{3})$/,"-$1")
	} else if (tel.length == 12) {
		tel=tel.replace(/(.{4})$/,"-$1")
	} else if (tel.length > 12) {
		tel=tel.replace(/(.{4})$/,"-$1")
	}
	return tel;
}

/* Redes Sociais */

$('#redes_sociais').mouseover(function(){
	$('.redes_sociais').animate({ 
		width: '500px',
		height: '300px'
	}, 500, 'linear');
})

$('#redes_sociais').mouseout(function(){
	$('.redes_sociais').animate({ 
		width: '100px',
		height: '60px'
	}, 500, 'linear');
})

/* Animações */

$(window).scroll(function(){
	if(window.scrollY+(0.8*$( window ).height())>$('.main_differential').position().top){
		$('.main_differential').removeClass('before-animated');
		$('.main_differential').addClass('animated');
		$('.main_differential').addClass('fadeIn');
	}
	if(window.scrollY+(0.8*$( window ).height())>$('.single_pricing').position().top){
		$('.single_pricing').removeClass('before-animated');
		$('.single_pricing').addClass('animated');
		$('.single_pricing').addClass('fadeInUp');
	}
	if(window.scrollY+(0.8*$( window ).height())>$('.main_contact_info').position().top){
		$('.main_contact_info').removeClass('before-animated');
		$('.main_contact_info').addClass('animated');
		$('.main_contact_info').addClass('fadeInLeft');
	}
	if(window.scrollY+(0.8*$( window ).height())>$('.single_contact_left').position().top){
		$('.single_contact_left').removeClass('before-animated');
		$('.single_contact_left').addClass('animated');
		$('.single_contact_left').addClass('fadeInRight');
	}
});

/* Formulário de Interesse */

/*$("#form_interesse").submit(function add_admin(event){
	$.ajax({
		dataType: "json",
		url: 	'https://app.fundacaocefetminas.org.br/formularioInteresse',
		xhrFields: { withCredentials: true },
	});
	return false;
});*/