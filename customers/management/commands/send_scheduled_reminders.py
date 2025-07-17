from django.core.management.base import BaseCommand
from django.utils import timezone
from customers.models import Reminder
from customers.views import send_whatsapp_reminder
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Process and send scheduled reminders"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Test run without actually sending reminders"
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help="Limit number of reminders to process"
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        now = timezone.now()
        
        # Get reminders due to be sent (within last 15 minutes to allow for delays)
        reminders = Reminder.objects.filter(
            status__in=['pending', 'scheduled'],
            scheduled_time__lte=now,
            scheduled_time__gte=now - timedelta(minutes=15)
        ).select_related('customer', 'customer__service_plan')
        
        if limit > 0:
            reminders = reminders[:limit]
        
        if not reminders.exists():
            logger.info("No reminders to process at this time")
            self.stdout.write("ℹ️ No reminders to process")
            return
        
        self.stdout.write(f"🔔 Processing {reminders.count()} reminders...")
        
        success_count = 0
        failure_count = 0
        
        for reminder in reminders:
            try:
                self.stdout.write(f"Processing reminder #{reminder.id} for {reminder.customer}")
                
                if dry_run:
                    self.stdout.write(f"DRY RUN: Would send to {reminder.customer.phone}")
                    success_count += 1
                    continue
                
                # Skip if customer has no service plan
                if not reminder.customer.service_plan:
                    reminder.status = 'failed'
                    reminder.message = "Customer has no service plan"
                    reminder.save()
                    failure_count += 1
                    continue
                
                # Attempt to send reminder
                sent = send_whatsapp_reminder(
                    customer=reminder.customer,
                    due_date=reminder.due_date,
                    amount=reminder.customer.service_plan.price,
                    send_at=reminder.scheduled_time
                )
                
                if sent:
                    reminder.status = 'sent'
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f"✅ Sent to {reminder.customer}"))
                else:
                    reminder.status = 'failed'
                    failure_count += 1
                    self.stdout.write(self.style.WARNING(f"⚠️ Failed for {reminder.customer}")))
                
                reminder.save()
                
            except Exception as e:
                logger.error(f"Error processing reminder {reminder.id}: {str(e)}")
                failure_count += 1
                self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"🎉 Completed: {success_count} successful, {failure_count} failed"
        ))