from core.utils import generate_hash
from .models import CallLog
from apps.branches.models import Branch
from apps.devices.models import Device


class CallLogService:

    @staticmethod
    def bulk_insert(data):

        branch = Branch.objects.get(code=data["branch_code"])
        device = Device.objects.get(device_id=data["device_id"])

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
