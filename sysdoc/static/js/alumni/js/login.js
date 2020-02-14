
/* Validação dos Formulários */

$("#form_login").validate({
	rules : {
		cpf:{
			required:true,
			minlength: 14
		},
		password:{
			required:true
		}
	},
	messages:{
		cpf:{
			required:"Informe o seu CPF!",
			minlength:"CPF inválido!"
		},
		password:{
			required:"Digite sua senha!"
		}
	}
});
