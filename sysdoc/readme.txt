- o GUnicorn que hospeda o módulo python com toda a aplicaćão na porta 8000, e gere toda distribuićão de carga entre os nucleos da máquina;
Comando para iniciar:
/home/fcmapp/Flask/sysdoc/init.sh *porta*

init.sh:
"/home/fcmapp/.local/bin/gunicorn -b 0.0.0.0:$1  --certfile fullchain.pem --keyfile privkey.pem --timeout 5000 --reload -w 4 wsgi" /https

- Um servićo de supervisor que consegue iniciar, reiniciar e logar todas requisićões ao sistema;
Arquivo de configuraćão em:
"/etc/supervisor/conf.d/sysfcm.conf"

sysfcm.conf:
"[program:sysfcm]
command=sh init.sh 8000
directory=/home/fcmapp/Flask/sysdoc/
stdout_logfile = /home/fcmapp/Flask/sysdoc/gunicorn_stdout.log
stderr_logfile = /home/fcmapp/Flask/sysdoc/gunicorn_stderr.log
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
"

Para reiniciar:
sudo supervisorctl reload //Recarrega todos servićos
sudo supervisorctl reread sysfcm //para o servićo, lê novamente o arquivo de configuraćao e inicia.
sudo supervisorctl restart sysfcm //apenas reinicia o servićo

-Por fim um servidor mais simples que é gerido pelo servićo Nginx que apenas escuta as portas 80 e 443 e redireciona ao GUnicorn (Que não consegue escutar em mais de uma porta sem ocupar pelo menos um nucleo de processamento)
Arquivo de configuraćão em:
"/etc/nginx/sites-enabled/fcmsys"

Comandos uteis:
sudo service nginx restart/start/stop


###########################################################
####################Certificados###########################
###########################################################
de 3 em 3 meses

Para renovar os certificados https:

sudo service nginx stop
sudo supervisorctl stop sysfcm
sudo service apache2 start

sudo certbot certonly --webroot -w /var/www/html
-d documentos.fundacaocefetminas.org.br
-d admin.fundacaocefetminas.org.br
-d conecta.fundacaocefetminas.org.br


Para ver o historico de comandos: history
Para filtrar o historico de comandos: history | grep certbot

sudo certbot certonly --webroot -w /var/www/html
-d admin.fundacaocefetminas.org.br
-d api.fundacaocefetminas.org.br
-d app.fundacaocefetminas.org.br
-d conecta.fundacaocefetminas.org.br
-d cursos.fundacaocefetminas.org.br
-d documentos.fundacaocefetminas.org.br
-d alumni.fundacaocefetminas.org.br
-d estagios.fundacaocefetminas.org.br
-d bi.fundacaocefetminas.org.br








cp /etc/letsencrypt/live/documentos.fundacaocefetminas.org.br/cert.pem /home/fcmapp/Flask/sysdoc
cp /etc/letsencrypt/live/documentos.fundacaocefetminas.org.br/fullchain.pem /home/fcmapp/Flask/sysdoc
cp /etc/letsencrypt/live/documentos.fundacaocefetminas.org.br/privkey.pem /home/fcmapp/Flask/sysdoc

sudo service apache2 stop
sudo service nginx start
sudo supervisorctl start sysfcm



###################### tutorial monica ###########################

verificar erros sistema ao vivo
tail /home/fcmapp/Flask/sysdoc/gunicorn_stderr.log

ultimos 10 erros sistema ao vivo
tail -f /home/fcmapp/Flask/sysdoc/gunicorn_stderr.log

ultimos 100 erros sistema ao vivo
tail -n 100 /home/fcmapp/Flask/sysdoc/gunicorn_stderr.log

tail -n 100 -f /home/fcmapp/Flask/sysdoc/gunicorn_stderr.log

ultimas 100 saídas do sistema ao vivo
tail -n 100 -f /home/fcmapp/Flask/sysdoc/gunicorn_stdout.log

ultimas 10 saídas ao vivo do sistema
tail -f /home/fcmapp/Flask/sysdoc/gunicorn_stdout.log

remover erros para nao encher
sudo rm /home/fcmapp/Flask/sysdoc/gunicorn_stderr.log

atualizar sistema
sudo supervisorctl reload sysfcm


sudo su
cd /etc/letsencrypt/live/
ls
cd documentos.fundacaocefetminas.org.br-0001/
ls
cat README
/etc/letsencrypt/live/documentos.fundacaocefetminas.org.br-0001# ls -la

###olhar data que foi feito o certificado para renovar
hexdigest

#####

sudo su
cd /etc/le
 cd /etc/letsencrypt/live/
 cd /etc/letsencrypt/live/documentos.fundacaocefetminas.org.br
ls
ls -la


### verificar

cat /home/fcmapp/Flask/sysdoc/restart.sh
