from main import application
from flask_sslify import SSLify

if __name__ == "__main__":
	application.run(host="0.0.0.0", port=443, threaded=True)
	sslify = SSLify(application, subdomains=True, permanent=True)
