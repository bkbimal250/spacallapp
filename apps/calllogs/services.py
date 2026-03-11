from django.db.models import Q
from core.utils import generate_hash
from .models import CallLog
from apps.branches.models import Branch
from apps.devices.models import Device
from apps.contacts.models import Contact


class CallLogService:

    @staticmethod
    def bulk_insert(data):

        branch = Branch.objects.get(code=data["branch_code"])
        device = Device.objects.get(device_id=data["device_id"])

        phone_numbers = {item["phone_number"] for item in data["call_logs"] if item.get("phone_number")}
        contact_map = {}

        if phone_numbers:
            contact_query = Q()
            for pn in phone_numbers:
                last_10 = pn[-10:] if len(pn) >= 10 else pn
                contact_query |= Q(phone_number__endswith=last_10)

            contacts = Contact.objects.filter(contact_query)
            for c in contacts:
                c_last_10 = c.phone_number[-10:] if len(c.phone_number) >= 10 else c.phone_number
                contact_map[c_last_10] = c

        objects = []

        for item in data["call_logs"]:
            phone_num = item["phone_number"]
            log_last_10 = phone_num[-10:] if phone_num and len(phone_num) >= 10 else phone_num

            call_hash = generate_hash(
                device.device_id,
                item["phone_number"],
                item["call_time"],
                item["duration"],
            )

            objects.append(
                CallLog(
                    branch=branch,
                    device=device,
                    contact=contact_map.get(log_last_10),
                    phone_number=item["phone_number"],
                    call_type=item["call_type"],
                    duration=item["duration"],
                    sim_slot=item["sim_slot"],
                    call_time=item["call_time"],
                    call_hash=call_hash,
                )
            )

        CallLog.objects.bulk_create(
            objects,
            batch_size=1000,
            ignore_conflicts=True,
        )
