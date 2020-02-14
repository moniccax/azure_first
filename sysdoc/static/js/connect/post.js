$(document).ready(function(){
	
	/* Detect Mobile */

	if( navigator.userAgent.match(/Android/i)
		|| navigator.userAgent.match(/webOS/i)
		|| navigator.userAgent.match(/iPhone/i)
		|| navigator.userAgent.match(/iPad/i)
		|| navigator.userAgent.match(/iPod/i)
		|| navigator.userAgent.match(/BlackBerry/i)
		|| navigator.userAgent.match(/Windows Phone/i)
		){
		$('.slide_next_btn_mobile').css('display', 'block');
		$('.slider_btn').css('display', 'none');
	}

	$('select').material_select();

	$('.slider').slider({
		indicators: false,
		interval: 1000000
	});

	$('.collapsible').off();
});

$('#slide_prev').click(function(){
	$('#post_slider').slider('prev');
});

$('#slide_next').click(function(){
	$('#post_slider').slider('next');
});

$("#form_new_comment").validate({
	rules: {
		new_comment: {
			required:true
		}
	},
	messages:{
		new_comment:{
			required:"Escreva um comentário!"
		}
	}
});

$('.comment_btn_menu').click(function(e){
	$('#comment_btn_overlay').toggleClass('modal-overlay');
	$('#comment_btn_overlay').css('z-index','1012');
	$('#comment_btn_overlay').css('display','block');
	$('#comment_btn_overlay').css('opacity','0.8');
	$(this).toggleClass('comment_btn_menu_active');
	$('.fixed-action-btn.horizontal ul').css('z-index', '2000');
});

$('.fixed-action-btn.horizontal ul').click(function(){
	$('#comment_btn_overlay').removeClass('modal-overlay');
	$('.comment_btn').removeClass('active');
	$('.comment_btn_menu').removeClass('comment_btn_menu_active');
});

let correctButton=function(){
	let scroll=window.scrollY+$(window).height();
	let seeFooter=$('body').height()-$('.page-footer').height();
	if (scroll>seeFooter){
		$('.fixed-action-btn').css('bottom',(scroll-seeFooter+40)+"px");
	}
	else{
		$('.fixed-action-btn').css('bottom',"40px");
	}
}

correctButton();
window.addEventListener('scroll', correctButton);