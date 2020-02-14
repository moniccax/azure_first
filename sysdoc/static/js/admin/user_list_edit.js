/* SELECT */

$(document).ready(function(){
	$('.select_ctg').material_select();
});

/* Imagem da Assinatura */

$(function(){
	$('#signatureimg').attr("src", $('#signatureimg').attr('src')+"?"+new Date().getTime());
});

/* Categorias  */

$(".add_admin_button").on('click',add_admin);

function add_admin(event){
	array=event.currentTarget.id.split('_');
	$.getJSON(
		'/lista_de_colaboradores/adicionar_administrador/'
		+array[array.length-2]+'/'+
		+array[array.length-1],
		{},
		function(data) {
			Materialize.toast(data.message, undefined, data.color);
			if(data.success){
				event.currentTarget.id="remove_admin_for_"+array[array.length-2]+'_'+array[array.length-1];
				$(event.currentTarget).tooltip('hide');
				$(event.currentTarget).attr('class', 'remove_admin_button tooltipped');
				$(event.currentTarget).html('<i class="material-icons" style="vertical-align:middle;">star</i>');
				$(event.currentTarget).off()
				$(event.currentTarget).on('click',remove_admin);
			}
		}
		);
	return false;
}

$(".remove_admin_button").on('click',remove_admin);

function remove_admin(event){
	array=event.currentTarget.id.split('_');
	$.getJSON(
		'/lista_de_colaboradores/remover_administrador/'
		+array[array.length-2]+'/'+
		+array[array.length-1],
		{},
		function(data) {
			Materialize.toast(data.message, undefined, data.color);
			if(data.success){
				event.currentTarget.id="add_admin_for_"+array[array.length-2]+'_'+	+array[array.length-1];
				$(event.currentTarget).tooltip('hide');
				$(event.currentTarget).attr('class', 'add_admin_button tooltipped');
				$(event.currentTarget).html('<i class="material-icons" style="vertical-align:middle;">star_border</i>');
				$(event.currentTarget).off()
				$(event.currentTarget).on('click',add_admin);
			}
		}
		);
	return false;
}

$(".add_category_button").on('click',add_category);

function add_category(event){
	array=event.currentTarget.id.split('_');
	user_id=array[array.length-1];
	cat_id=$("#category_value_"+user_id).val();
	$.getJSON(
		'/lista_de_colaboradores/adicionar_categoria/'
		+user_id+'/'+
		cat_id,
		{},
		function(data) {
			Materialize.toast(data.message, undefined, data.color);
			if(data.success){
				newdiv='<div class="chip">';
				newdiv+='<font class="panton-bold" color="#000">'+$("#category_value_"+user_id).find(":selected").text();
				newdiv+='<a class="add_admin_button tooltipped" id="add_admin_for_'+user_id+'_'+cat_id+'" href="#" data-position="top" data-tooltip="Tornar administrador" style="color:gray">';
				newdiv+='<i class="material-icons" style="vertical-align:middle;" >star_border</i>';
				newdiv+='</a> <i class="remove_category_button close material-icons tooltipped" id="remove_category_for_'+user_id+'_'+cat_id+'" data-position="top" data-tooltip="Remover categoria" style="color:gray">close</i>';
				$(".categories_attached_to_user_"+user_id).append(newdiv);
				$("#add_admin_for_"+user_id+"_"+cat_id).on('click',add_admin);
				$("#remove_category_for_"+user_id+"_"+cat_id).on('click',remove_category);
			}
		}
		);
	return false;
}

$(".remove_category_button").on('click',remove_category);

function remove_category(event){
	array=event.currentTarget.id.split('_');
	user_id=array[array.length-2];
	cat_id=array[array.length-1];
	$.getJSON(
		'/lista_de_colaboradores/remover_categoria/'
		+user_id+'/'+
		cat_id,
		{},
		function(data) {
			Materialize.toast(data.message, undefined, data.color);
			if(data.success){
				$('#'+event.currentTarget.id).tooltip('hide');
				$('#'+event.currentTarget.id).parents('.chip').remove();
			}
		}
		);
	return false;
}
