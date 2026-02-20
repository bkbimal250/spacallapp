from .models import Branch


class BranchService:

    @staticmethod
    def create_branch(data):
        return Branch.objects.create(**data)

    @staticmethod
    def update_branch(instance, data):
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    @staticmethod
    def deactivate_branch(instance):
        instance.is_active = False
        instance.save()
        return instance
