import logging
from django.conf import settings
from whatsapp_api_client_python import API
from .models import WhatsAppMessage

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.client = API.GreenAPI(
            settings.WHATSAPP_API_ID,
            settings.WHATSAPP_API_TOKEN
        )
    
    def send_message(self, customer, message):
        try:
            phone = self._format_phone(customer.phone)
            if not phone:
                raise ValueError("Invalid phone number")
            
            response = self.client.sending.sendMessage(
                f"{phone}@c.us",
                message
            )
            
            # Save message record
            WhatsAppMessage.objects.create(
                customer=customer,
                message=message,
                status='sent' if response.code == 200 else 'failed',
                whatsapp_id=response.id if response.code == 200 else None,
                error=None if response.code == 200 else response.message
            )
            
            return response.code == 200
            
        except Exception as e:
            logger.error(f"WhatsApp send error: {str(e)}")
            WhatsAppMessage.objects.create(
                customer=customer,
                message=message,
                status='failed',
                error=str(e)
            )
            return False
    
    def _format_phone(self, phone):
        # Remove all non-digit characters
        cleaned = ''.join(filter(str.isdigit, str(phone)))
        if cleaned.startswith('0'):
            cleaned = '92' + cleaned[1:]  # Pakistan country code
        return cleaned if len(cleaned) >= 11 else None