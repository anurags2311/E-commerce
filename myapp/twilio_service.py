from twilio.rest import Client
from django.conf import settings

def send_sms(to, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER, settings.TWILIO_VERIFY_SERVICE_SID)
    
    message = client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=to
    )

    return message.sid