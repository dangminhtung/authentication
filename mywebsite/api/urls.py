from django.urls import path
from .views import createAS,getAS, UserInfoHashView,RegisterView,LoginView,VerifyToken,checkPermissionAS,getAllAS,getAllUser,getAllAccount,CreateAccessLog,getAllAccessLog,CreateQRCode, updateUser,RegenerateQRCode,deleteUser



urlpatterns = [
    path('register/',RegisterView.as_view(),name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('verify-token/',VerifyToken.as_view(),name='viewUser'),
    path('accountASPermission/<int:user_id>/', checkPermissionAS.as_view(), name='account-as-permission'),
    path('getAllUser/', getAllUser.as_view(), name='get_All_User'),
    path('updateUser/<str:id_user>/', updateUser.as_view(), name='update User'),
    path('deleteUser/<str:id_user>/', deleteUser.as_view(), name='delete User'),
    path('getAllAccount/',getAllAccount.as_view(),name='get_ALL_Account'),
    path('hash/', UserInfoHashView.as_view(), name='user_info_hash'),
    path('hashV2/', CreateQRCode.as_view(), name='Create QR Code'),
    path('reregenerateqrCode/', RegenerateQRCode.as_view(), name='Regenerate QR Code'),
    path('createAS/',createAS.as_view(),name='create_AS'),
    path('getAS/',getAS.as_view(), name='getAS'),
    path('getAllAS/',getAllAS.as_view(),name='get All AS'),
    path('createLogAccess/',CreateAccessLog.as_view(),name='create Access Log'),
    path('getAllAccessLog/', getAllAccessLog.as_view(), name='getAllAccessLog')
]
