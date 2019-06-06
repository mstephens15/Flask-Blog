import os
class Config:
	SECRET_KEY = '5791628bb0b13ce0c676dfde280ba245'

	#Making an easy, local database
	SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
	
	#Mail
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	MAIL_USERNAME = 'mtchllstphns@gmail.com'
	MAIL_PASSWORD = 'Dudley15!!'