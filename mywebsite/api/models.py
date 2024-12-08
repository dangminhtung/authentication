from django.db import models
import json
from .encrypt_data import generateKeyEncrypted,generateKeySign


# Create your models here.
class UserInfo(models.Model):
    id_user = models.CharField(max_length=100, primary_key=True)
    id_qr = models.TextField(max_length=255, default="QR123")
    name = models.CharField(max_length=100)
    dob = models.CharField(max_length=255)
    address = models.CharField(max_length=255 , default="Hà Nội")
    numberPhone = models.CharField(max_length=255,default="0123456789")
    email = models.CharField(max_length=255, default="user@gmail.com")
    image=models.TextField(null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
class AS(models.Model):
    id_as=models.BigAutoField(primary_key=True)
    nameAS=models.CharField(max_length=100)
    address=models.CharField(max_length=255, default='Ha Noi')
    encrypt_key=models.JSONField()
    Sign_key=models.JSONField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.encrypt_key=json.dumps(generateKeyEncrypted())
        self.Sign_key=json.dumps(generateKeySign())
        super().save(*args, **kwargs)
class User_Account(models.Model):
    id_account=models.BigAutoField(primary_key=True)
    email=models.CharField(max_length=255, unique=True)
    name=models.CharField(max_length=255)
    password=models.CharField(max_length=255,unique=True)
    is_superAdmin=models.BooleanField(default=False)
    
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=[]
class AccountASPermission(models.Model):
    account=models.ForeignKey(User_Account,on_delete=models.CASCADE)
    as_object=models.ForeignKey(AS,on_delete=models.CASCADE)
class AccessLog(models.Model):
    id_AL= models.BigAutoField(primary_key=True)
    id_user=models.ForeignKey(UserInfo,on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    dob = models.CharField(max_length=255)
    created_at=models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255)
class Hash(models.Model):
    idHash = models.BigAutoField(primary_key=True)
    id_qr = models.TextField(max_length=255, default="QR123")
    value_hash=models.CharField(max_length=255)
