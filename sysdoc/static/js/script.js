
const applicationServerPublicKey = 'BE-dBCI0u0c4IWjovy7x7RKdJThH5fY9k8yGmKo_V3u7WnOhFWy1BSDJ6TuGHaVVd0nfd7kj3SGIGnaNvem3wfc';

let isSubscribed = false;
let swRegistration = null;

function urlB64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/serviceworker.js').then(function(registration) {
      // Registration was successful
      console.log('ServiceWorker registration successful with scope: ', registration);
			swRegistration = registration;
			registerToPushNotification();
    }, function(err) {
      // registration failed :(
      console.log('ServiceWorker registration failed: ', err);
    });
  });
}

function registerToPushNotification(){
	subscribeUser();
	swRegistration.pushManager.getSubscription().then(function(subscription) {
    isSubscribed = !(subscription === null);
    updateSubscriptionOnServer(subscription);

    if (isSubscribed) {
      console.log('User IS subscribed.');
    } else {
      console.log('User is NOT subscribed.');
    }
  });
}

function subscribeUser() {
  const applicationServerKey = urlB64ToUint8Array(applicationServerPublicKey);
  swRegistration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: applicationServerKey
  })
  .then(function(subscription) {
    console.log('User is subscribed:', subscription);
    updateSubscriptionOnServer(subscription);
    isSubscribed = true;
  })
  .catch(function(err) {
    console.log('Failed to subscribe the user: ', err);
  });
}

function updateSubscriptionOnServer(subscription) {
  if (subscription) {
		let xhr = new XMLHttpRequest();
		xhr.open("POST", "/admin/register_push", true);
		xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
		xhr.send(JSON.stringify(subscription));
  }
}

$(document).ready(function(){

	if (window.location.href.split('.')[0].split('/')[2]=="app"){
		let anchors = document.querySelectorAll("a");
		for (let i = 0; i < anchors.length; i++) {
				let original =anchors[i].href;
				let service=anchors[i].href.split('.')[0].split('/')[2];
				if(service=="documentos" || service=="conecta" || service=="admin"){
					let uri= anchors[i].href.split('.br')[1];
		    	anchors[i].href = "https://app.fundacaocefetminas.org.br/"+service+uri;
				}
		}

		let forms = document.querySelectorAll("form");
		for (let i = 0; i < forms.length; i++) {
			if(typeof forms[i].action == "string"){
				let service=forms[i].action.split('.')[0].split('/')[2];
				if(service=="documentos" || service=="conecta" || service=="admin"){
					let uri= forms[i].action.split('.br')[1];
		    	forms[i].action = "https://app.fundacaocefetminas.org.br/"+service+uri;
				}
			}
		}
	}

	if(( navigator.userAgent.match(/Android/i)
		|| navigator.userAgent.match(/webOS/i)
		|| navigator.userAgent.match(/iPhone/i)
		|| navigator.userAgent.match(/iPad/i)
		|| navigator.userAgent.match(/iPod/i)
		|| navigator.userAgent.match(/BlackBerry/i)
		|| navigator.userAgent.match(/Windows Phone/i)
	) && window.location.href.split('.')[0].split('/')[2]!="app") {
			let service=window.location.href.split('.')[0].split('/')[2];
			let uri= window.location.href.split('.br')[1];
		  location.replace("https://app.fundacaocefetminas.org.br/"+service+uri);
	}

	/* Menu - Mobile */

	$(".button-collapse").sideNav();

	/* Menu - Dropdown */

	$('.dropdown-button').dropdown({
		belowOrigin: true,
		hover: true,
	});

	/* Tooltip */

	$('.tooltipped').tooltip({delay: 50});

	/* Modal */

	$('.modal').modal();

	/* Select - Restore */

	$('#file_name').material_select();

	/* Detect Mobile */

	if( navigator.userAgent.match(/Android/i)
		|| navigator.userAgent.match(/webOS/i)
		|| navigator.userAgent.match(/iPhone/i)
		|| navigator.userAgent.match(/iPad/i)
		|| navigator.userAgent.match(/iPod/i)
		|| navigator.userAgent.match(/BlackBerry/i)
		|| navigator.userAgent.match(/Windows Phone/i)
	){
		$('.material-tooltip').css('display', 'none');
		$('#toast-container').css('right', '0');
		$('#toast-container').css('bottom', '0');
		$('.iframe_mobile').remove();
		$('.img_iframe').css('display', 'block');
		$('.img_tutorial').css('width','100%');
		$('.img_tutorial').css('height','auto');
	}
});

/* Feedback - Remover Toast */

$(document).on('click', '#toast-container .toast', function() {
	$(this).fadeOut(function(){
		$(this).remove();
	});
});

/* Submenu de ícones */

$('#sistema').click(function() {
	$('#submenu_id').removeClass("hide");
	$('#submenu_system').removeClass("hide");
	$('#submenu_profile').addClass("hide");
	$('#submenu_employee').addClass("hide");
	$('#submenu_settings').addClass("hide");
	//$('.logo_white').css("opacity","0.2");
	$('#sistema').css("color","#ed3237");
	$('#perfil').css("color","#213f63");
	//$('#colaboradores').css("color","#fff");
	//$('#configuracoes').css("color","#fff");
	$('#colaboradores').css("color","#213f63");
	$('#configuracoes').css("color","#213f63");
});

/*let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent Chrome 67 and earlier from automatically showing the prompt
  e.preventDefault();
  // Stash the event so it can be triggered later.
  deferredPrompt = e;
});

$('#downloadapp').click(function() {
	deferredPrompt.prompt();
	  // Wait for the user to respond to the prompt
	  deferredPrompt.userChoice
	    .then((choiceResult) => {
	      if (choiceResult.outcome === 'accepted') {
	        console.log('User accepted the A2HS prompt');
	      } else {
	        console.log('User dismissed the A2HS prompt');
	      }
	      deferredPrompt = null;
	    });
});*/

$('#perfil').click(function() {
	$('#submenu_id').removeClass("hide");
	$('#submenu_profile').removeClass("hide");
	$('#submenu_system').addClass("hide");
	$('#submenu_employee').addClass("hide");
	$('#submenu_settings').addClass("hide");
	//$('.logo_white').css("opacity","0.2");
	$('#perfil').css("color","#ed3237");
	//$('#colaboradores').css("color","#fff");
	//$('#configuracoes').css("color","#fff");
	$('#sistema').css("color","#213f63");
	$('#colaboradores').css("color","#213f63");
	$('#configuracoes').css("color","#213f63");
});

$('#colaboradores').click(function() {
	$('#submenu_id').removeClass("hide");
	$('#submenu_employee').removeClass("hide");
	$('#submenu_system').addClass("hide");
	$('#submenu_profile').addClass("hide");
	$('#submenu_settings').addClass("hide");
	//$('.logo_white').css("opacity","0.2");
	$('#colaboradores').css("color","#ed3237");
	//$('#perfil').css("color","#fff");
	//$('#configuracoes').css("color","#fff");
	$('#sistema').css("color","#213f63");
	$('#perfil').css("color","#213f63");
	$('#configuracoes').css("color","#213f63");
});

$('#configuracoes').click(function() {
	$('#submenu_id').removeClass("hide");
	$('#submenu_settings').removeClass("hide");
	$('#submenu_system').addClass("hide");
	$('#submenu_profile').addClass("hide");
	$('#submenu_employee').addClass("hide");
	//$('.logo_white').css("opacity","0.2");
	$('#configuracoes').css("color","#ed3237");
	//$('#perfil').css("color","#fff");
	//$('#colaboradores').css("color","#fff");
	$('#sistema').css("color","#213f63");
	$('#perfil').css("color","#213f63");
	$('#colaboradores').css("color","#213f63");
});

$('#submenu_id').click(function() {
	$('#submenu_id').addClass("hide");
	//$('.logo_white').css("opacity","1");
	//$('#perfil').css("color","#fff");
	//$('#colaboradores').css("color","#fff");
	//$('#configuracoes').css("color","#fff");
	$('#sistema').css("color","#213f63");
	$('#perfil').css("color","#213f63");
	$('#colaboradores').css("color","#213f63");
	$('#configuracoes').css("color","#213f63");
});
