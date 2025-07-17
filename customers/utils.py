# customers/utils.py

def send_whatsapp_reminder(customer, due_date, amount, send_at=None):
    phone = customer.phone
    name = customer.name
    message = f"Hi {name}, your internet bill of ₹{amount} is due on {due_date}. Kindly pay on time to avoid service interruption."

    print(f"📤 Sending WhatsApp to {phone} at {send_at}: {message}")
    # Optionally, integrate with pywhatkit, Twilio, etc.
    # Example:
    # import pywhatkit as kit
    # hour = send_at.hour
    # minute = send_at.minute
    # kit.sendwhatmsg(phone, message, hour, minute, wait_time=10)
