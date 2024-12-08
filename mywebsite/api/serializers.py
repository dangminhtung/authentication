from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import AS, UserInfo,User_Account,AccountASPermission,AccessLog

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserInfo  
        fields=["id_user","id_qr","name","dob","address","numberPhone","email","image"]
        read_only_fields = ["created_at", "updated_at"]
class ASSerializer(serializers.ModelSerializer):
    class Meta:
        model=AS
        fields=['id_as','nameAS','address','created_at','updated_at','encrypt_key','Sign_key']
        read_only_fields=['created_at','updated_at','encrypt_key','Sign_key']

class AccountSerializer(serializers.ModelSerializer):
    id_as=serializers.PrimaryKeyRelatedField(queryset=AS.objects.all(),required=False, write_only=True)
    class Meta:
        model=User_Account
        fields=["name","email","password","is_superAdmin","id_as"]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    def validate(self, data):
        id_as = data.get('id_as')
        is_superAdmin = data.get('is_superAdmin', False)

        if id_as is None and not is_superAdmin:
            raise serializers.ValidationError("You must provide either 'id_as' or 'is_superAdmin'.")

        return data
    def create(self, validated_data):
        id_as=validated_data.pop('id_as',None)
        is_superAdmin=validated_data.get('is_superAdmin',False)
        
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.password=make_password(password)
        instance.save()
        if not is_superAdmin and id_as:
            AccountASPermission.objects.create(account=instance,as_object=id_as)

        return instance
class AccountASPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountASPermission
        fields = ['as_object']
class AccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessLog
        fields=["id_user","name","dob","created_at","status"]
        read_only_fields = ["created_at"]