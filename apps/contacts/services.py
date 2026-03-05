from .models import Contact
from apps.calllogs.models import CallLog

class ContactService:
    @staticmethod
    def create_contact(data, user):
        data['created_by'] = user
        data['updated_by'] = user
        contact = Contact.objects.create(**data)
        
        CallLog.objects.filter(phone_number=contact.phone_number).update(contact=contact)
        return contact

    @staticmethod
    def update_contact(instance, data, user):
        data['updated_by'] = user
        old_phone_number = instance.phone_number
        
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        
        new_phone_number = instance.phone_number
        if old_phone_number != new_phone_number:
            CallLog.objects.filter(contact=instance).update(contact=None)
            CallLog.objects.filter(phone_number=new_phone_number).update(contact=instance)
            
        return instance

    @staticmethod
    def delete_contact(instance):
        instance.delete()