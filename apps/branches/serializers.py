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
    # Added branch_group_name for easier UI consumption
    branch_group_name = serializers.CharField(source='branch_group.name', read_only=True)

    class Meta:
        model = Branch
        fields = '__all__'
