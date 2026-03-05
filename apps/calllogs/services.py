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

        phone_numbers = {item["phone_number"] for item in data["call_logs"]}
        contacts = Contact.objects.filter(phone_number__in=phone_numbers)
        contact_map = {c.phone_number: c for c in contacts}

        objects = []

        for item in data["call_logs"]:
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
                    contact=contact_map.get(item["phone_number"]),
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
