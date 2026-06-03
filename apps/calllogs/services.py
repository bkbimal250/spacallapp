from django.db import models
from django.db.models import Q, F
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
            raw_phone = item.get("phone_number", "")
            # Clean non-digits
            import re
            phone_num = re.sub(r'\D', '', raw_phone)
            log_last_10 = phone_num[-10:] if len(phone_num) >= 10 else phone_num

            # Store the original formatted number but use the cleaned version for internal logic if needed
            # Actually, let's keep the original for display, but ensure matching uses standardized logic
            
            call_hash = generate_hash(
                device.device_id,
                raw_phone,
                item["call_time"],
                item["duration"],
            )

            # Pre-calculate normalized phone for fast matching
            import re
            clean_digits = re.sub(r'\D', '', item.get("phone_number", ""))
            phone_normalized = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits

            objects.append(
                CallLog(
                    branch=branch,
                    device=device,
                    contact=contact_map.get(log_last_10),
                    phone_number=item["phone_number"],
                    phone_normalized=phone_normalized,
                    call_type=item["call_type"],
                    duration=item["duration"],
                    sim_slot=item["sim_slot"],
                    call_time=item["call_time"],
                    call_hash=call_hash,
                )
            )

        # Use ignore_conflicts=True to handle duplicates safely
        created_objects = CallLog.objects.bulk_create(
            objects,
            batch_size=1000,
            ignore_conflicts=True,
        )

        # Post-processing: Tracking for Follow-ups and SLA
        # Since created_objects might not contain IDs when ignore_conflicts=True (backend dependent),
        # we fetch the recently created records using the Hashes we just generated.
        hashes = [obj.call_hash for obj in objects]
        inserted_logs = CallLog.objects.filter(call_hash__in=hashes)

        FollowUpService.process_batch(inserted_logs)


class FollowUpService:
    @staticmethod
    def process_batch(call_logs):
        """
        Processes a batch of call logs to:
        1. Create tracking entries for missed calls.
        2. Match outgoing calls to pending missed calls.
        """
        from .models import MissedCallFollowUp
        from django.utils import timezone
        from datetime import timedelta

        # 1. Handle Missed Calls (Create tracking entries AND resolve if resolving call exists)
        missed_logs = [log for log in call_logs if log.call_type == "missed"]
        if missed_logs:
            for m_log in missed_logs:
                followup, created = MissedCallFollowUp.objects.get_or_create(
                    missed_call=m_log,
                    defaults={'branch': m_log.branch, 'is_followed_up': False}
                )
                
                if created:
                    # Check if an outgoing or incoming call already exists in the DB for this number AFTER this missed call
                    # (This handles the case where the resolving call was synced before the missed call)
                    existing_followup_call = CallLog.objects.filter(
                        branch=m_log.branch,
                        phone_normalized=m_log.phone_normalized,
                        call_type__in=["outgoing", "incoming"],
                        call_time__gt=m_log.call_time
                    ).order_by('call_time').first()

                    if existing_followup_call:
                        # Resolve immediately
                        if existing_followup_call.call_type == "incoming":
                            status = "CUSTOMER_RECALL"
                        else:
                            time_diff = existing_followup_call.call_time - m_log.call_time
                            diff_minutes = time_diff.total_seconds() / 60
                            status = "GOOD" if diff_minutes <= 10 else "OK" if diff_minutes <= 30 else "LATE" if diff_minutes <= 60 else "MISSED"
                        
                        followup.followup_call = existing_followup_call
                        followup.is_followed_up = True
                        followup.first_followup_time = existing_followup_call.call_time
                        followup.followup_attempt_count = 1
                        followup.sla_status = status
                        followup.save()
                    else:
                        # Schedule notification tasks normally
                        from .tasks import schedule_missed_call_notifications
                        schedule_missed_call_notifications.delay(m_log.id)

        # 2. Handle Outgoing and Incoming Calls (Resolve pending follow-ups)
        resolving_logs = [log for log in call_logs if log.call_type in ["outgoing", "incoming"]]
        for r_log in resolving_logs:
            # Find all pending missed calls for this number (normalized) and branch that happened BEFORE this resolving call.
            pendings = MissedCallFollowUp.objects.filter(
                branch=r_log.branch,
                missed_call__phone_normalized=r_log.phone_normalized,
                missed_call__call_time__lt=r_log.call_time,
                is_followed_up=False
            ).select_related('missed_call')

            for pending in pendings:
                # Calculate SLA Status
                if r_log.call_type == "incoming":
                    status = "CUSTOMER_RECALL"
                else:
                    time_diff = r_log.call_time - pending.missed_call.call_time
                    diff_minutes = time_diff.total_seconds() / 60
                    status = "GOOD" if diff_minutes <= 10 else "OK" if diff_minutes <= 30 else "LATE" if diff_minutes <= 60 else "MISSED"

                pending.followup_call = r_log
                pending.is_followed_up = True
                pending.first_followup_time = r_log.call_time
                pending.followup_attempt_count += 1
                pending.sla_status = status
                pending.save()

            if r_log.call_type == "outgoing":
                # Increment attempt count for all historical missed calls for this number
                MissedCallFollowUp.objects.filter(
                    branch=r_log.branch,
                    missed_call__phone_normalized=r_log.phone_normalized,
                    missed_call__call_time__lt=r_log.call_time
                ).update(followup_attempt_count=models.F('followup_attempt_count') + 1)
