from django.core import mail
from django.conf import settings
from django.core.management.base import BaseCommand
class Mailer(BaseCommand):
	help = "To send Email"

	def user_reg_notify(self, user):
		try:

			from_email = "rapidsms@rapidsms.moh.gov.rw"
			subject = "Confirm Your Login Account in RapidSMS Rwanda"
			message = "Dear %s,\n This is to let you know that you are now registered in RapidSMS Rwanda System. Your username is '%s', and your email in RapidSMS is '%s', and the default password is already set for you, but please use this link http://%s:%s/account/password_reset/ to reset it before you can login in." % (user.get_full_name(), user.username, user.email, "rapidsms.moh.gov.rw", settings.SERVER_PORT)
			connection = mail.get_connection()
			connection.open()
			email = mail.EmailMessage(subject, message, from_email,[user.email], connection=connection)
			#print email
			email.send()
			connection.close()
		except Exception, e:
			pass#print e#pass
		return True

