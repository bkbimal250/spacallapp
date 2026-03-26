from rest_framework import serializers
from .models import Branch, BranchGroups

class BranchGroupSerializer(serializers.ModelSerializer):
    branch_count = serializers.SerializerMethodField()

    class Meta:
        model = BranchGroups
        fields = '__all__'

    def get_branch_count(self, obj):
        return obj.branches.count()

class BranchSerializer(serializers.ModelSerializer):
    branch_group_name = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = '__all__'

    def get_branch_group_name(self, obj):
        if obj.branch_group:
            return obj.branch_group.name
        return None
