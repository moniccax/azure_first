$(document).ready(function(){
	$('.select_user').material_select();
	$('.select_category').material_select();

	$("#contexts_table").DataTable();
	$("#employee_table").DataTable();
});

/* Tabelas */

$(function () {
	if ($('#contexts_table').length > 0) {
        $('#contexts_table_filter').empty();
        $('#contexts_table_filter').append(
        	"<div class='input-field' style='width: 30%; margin-left: 5%;'>" +
        	"    <input type='search' class='validate' id='search_table_ctx'/>" +
        	"    <label for='search_table_ctx' class='ms_medium'>Pesquisar</label>" +
        	"</div>")
    }

    $("#search_table_ctx").keyup(function(){
    	var oTable = $('#contexts_table').dataTable();
    	oTable.fnFilter($(this).val());
    } ) ;
});

$(function () {
	if ($('#employee_table').length > 0) {
        $('#employee_table_filter').empty();
        $('#employee_table_filter').append(
        	"<div class='input-field' style='width: 30%; margin-left: 5%;'>" +
        	"    <input type='search' class='validate' id='search_table_emp'/>" +
        	"    <label for='search_table_emp' class='ms_medium'>Pesquisar</label>" +
        	"</div>")
    }

    $("#search_table_emp").keyup(function(){
    	var oTable = $('#employee_table').dataTable();
    	oTable.fnFilter($(this).val());
    });
});

$(".add_admin_button").on('click',add_admin);

function add_admin(event){
			array=event.currentTarget.id.split('_');
			$.ajax({
				dataType: "json",
				url: 	'https://admin.fundacaocefetminas.org.br/lista_de_colaboradores/adicionar_administrador/'+array[array.length-2]+'/'+array[array.length-1],
				xhrFields: { withCredentials: true },
				success: (data) =>
				{
					toastContent = $(data.message).add($('<button class="btn-flat toast-action"><i class="material-icons">clear</i></button>'));
					Materialize.toast(toastContent, undefined, data.color);
					if(data.success){
						event.currentTarget.id="remove_admin_for_"+array[array.length-2]+'_'+array[array.length-1];
						$(event.currentTarget).tooltip('hide');
						$(event.currentTarget).attr('class', 'remove_admin_button tooltipped');
						$(event.currentTarget).html('<i class="material-icons" style="vertical-align:middle;">star</i>');
						$(event.currentTarget).off()
						$(event.currentTarget).on('click',remove_admin);
					}
				}
			});
			return false;
}

$(".remove_admin_button").on('click',remove_admin);

function remove_admin(event){
			array=event.currentTarget.id.split('_');

			$.ajax({
				dataType: "json",
				url: 	'https://admin.fundacaocefetminas.org.br/lista_de_colaboradores/remover_administrador/'
				+array[array.length-2]+'/'+
				+array[array.length-1],
				xhrFields: { withCredentials: true },
				success: (data) =>
				{
					toastContent = $(data.message).add($('<button class="btn-flat toast-action"><i class="material-icons">clear</i></button>'));
					Materialize.toast(toastContent, undefined, data.color);
					if(data.success){
						event.currentTarget.id="add_admin_for_"+array[array.length-2]+'_'+	+array[array.length-1];
						$(event.currentTarget).tooltip('hide');
						$(event.currentTarget).attr('class', 'add_admin_button tooltipped');
						$(event.currentTarget).html('<i class="material-icons" style="vertical-align:middle;">star_border</i>');
						$(event.currentTarget).off()
						$(event.currentTarget).on('click',add_admin);
					}
				}
			});
			return false;
}

$(".add_category_button").on('click',add_category);

function add_category(event){
	array=event.currentTarget.id.split('_');
	cat_id=array[array.length-1];
	user_id=$("#user_value_"+cat_id).val();

	$.ajax({
		dataType: "json",
		url: 	'https://admin.fundacaocefetminas.org.br/lista_de_colaboradores/adicionar_categoria/'
		+user_id+'/'+
		cat_id,
		xhrFields: { withCredentials: true },
		success: (data) =>
		{
			toastContent = $(data.message).add($('<button class="btn-flat toast-action"><i class="material-icons">clear</i></button>'));
			Materialize.toast(toastContent, undefined, data.color);
			if(data.success){
				newdiv='<div class="chip">';
				newdiv+='<font class="panton-bold" color="#000">'+$("#user_value_"+cat_id).find(":selected").text();
				newdiv+='<a class="add_admin_button tooltipped" id="add_admin_for_'+user_id+'_'+cat_id+'" href="#" data-position="top" data-tooltip="Tornar administrador" style="color:gray">';
				newdiv+='<i class="material-icons" style="vertical-align:middle;" >star_border</i>';
				newdiv+='</a> <i class="remove_category_button close material-icons tooltipped" id="remove_category_for_'+user_id+'_'+cat_id+'" data-position="top" data-tooltip="Remover categoria" style="color:gray">close</i>';
				$(".users_attached_to_category_"+cat_id).append(newdiv);
				$("#add_admin_for_"+user_id+"_"+cat_id).on('click',add_admin);
				$("#remove_category_for_"+user_id+"_"+cat_id).on('click',remove_category);
			}
		}
	});
	return false;
}

$(".remove_category_button").on('click',remove_category);

function remove_category(event){
	array=event.currentTarget.id.split('_');
	user_id=array[array.length-2];
	cat_id=array[array.length-1];
	$.ajax({
		dataType: "json",
		url: 	'https://admin.fundacaocefetminas.org.br/lista_de_colaboradores/remover_categoria/'
			+user_id+'/'+
			cat_id,
		xhrFields: { withCredentials: true },
		success: (data) =>
		{
			toastContent = $(data.message).add($('<button class="btn-flat toast-action"><i class="material-icons">clear</i></button>'));
			Materialize.toast(toastContent, undefined, data.color);
			if(data.success){
				$('#'+event.currentTarget.id).tooltip('hide');
				$('#'+event.currentTarget.id).parents('.chip').remove();
			}
		}
	});
	return false;
}

$(".virtualcb").on('change',function(){
		var val = $(this).is(':checked') ? 'checked' : 'unchecked';
		if(val=="checked"){
			$("#"+$(this).attr("id").split("_").slice(1).join("_")).prop("checked", true);
		}
		else{
			$("#"+$(this).attr("id").split("_").slice(1).join("_")).prop("checked", false);
		}
});


let correctButton=function(){
	let scroll=window.scrollY+$(window).height();
	let seeFooter=$('body').height()-$('.page-footer').height();
	if (scroll>seeFooter){
		$('.btn_fixed').css('bottom',(scroll-seeFooter+40)+"px");
	}
	else{
		$('.btn_fixed').css('bottom',"40px");
	}
}

correctButton();
window.addEventListener('scroll', correctButton);
