from .services import send_website_lead_notification


def send_website_lead_notification_task(lead_id):
    from .models import WebsiteLead

    lead = WebsiteLead.objects.select_related("branch").get(pk=lead_id)
    return send_website_lead_notification(lead)
