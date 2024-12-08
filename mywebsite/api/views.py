from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import check_password
from rest_framework import status
from .serializers import ASSerializer, UserInfoSerializer,AccountSerializer,AccountASPermissionSerializer,AccessLogSerializer
from .models import AS,User_Account, AccountASPermission,UserInfo,AccessLog
import base64, json
from .encrypt_data import encode_face,encode_info,sign_data,encode_infoV2
import jwt,datetime
from django.http import JsonResponse
from .qrcodegen import QrCode
from PIL import Image
from io import BytesIO
import random



class RegisterView(APIView):
    def post(self,request, *args, **kwargs):
        serializer=AccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
class LoginView(APIView):
    def post(self,request):
        email=request.data['email']
        password=request.data['password']
        user=User_Account.objects.filter(email=email).first()

        if user is None :
            raise AuthenticationFailed("User not Found!")
        if not check_password(password,user.password):
            raise AuthenticationFailed("incorrect password")
        payload={
            'id': user.id_account,
            'is_superAdmin':user.is_superAdmin,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'jwt': token
        }
        return response
    
from rest_framework.exceptions import NotFound
class checkPermissionAS(generics.GenericAPIView):
    serializer_class=AccountASPermissionSerializer
    def get(self, request,user_id):
        try:
            permissions=AccountASPermission.objects.filter(account=user_id)
            if not permissions.exists():
                raise NotFound('No permissions found for this user.')
            serializer = self.get_serializer(permissions, many=True)
            return Response(serializer.data)
        except AccountASPermission.DoesNotExist:
            raise NotFound('User does not exist.')
class VerifyToken(APIView):
    def get(self, request):
        auth_header = request.headers.get('Authorization')
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
             return JsonResponse({'error': 'Token đã hết hạn'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Token không hợp lệ'}, status=401)
        user = User_Account.objects.filter(id_account=payload['id']).first()
        serializer = AccountSerializer(user)
        return Response(serializer.data)
class getAllUser(APIView):
    def get(self,request):
        try:
            data=UserInfo.objects.all()
            data_serializer=UserInfoSerializer(data,many=True)
        except UserInfo.DoesNotExist:
            return Response({'error': 'No info'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data_serializer.data,status=status.HTTP_200_OK)
class updateUser(APIView):
    def put(self, request, id_user):
        try:
            # Lấy thông tin người dùng theo id_user
            user = UserInfo.objects.get(id_user = id_user)
        except UserInfo.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Sử dụng serializer để validate và cập nhật dữ liệu
        serializer = UserInfoSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"data":"success"},status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class deleteUser(APIView):
    def delete(self,request,id_user):
        try:
            data_user= UserInfo.objects.get(id_user = id_user)
        except UserInfo.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        from .models import Hash
        Hash.objects.filter(id_qr = data_user.id_qr).delete()
        UserInfo.objects.filter(id_user = id_user).delete()
        return Response({"data":"success"},status=status.HTTP_200_OK)
class getAllAccount(APIView):
    def get(self,request):
        try:
            data=User_Account.objects.all()
            data_serializer=AccountSerializer(data,many=True)
        except UserInfo.DoesNotExist:
            return Response({'error': 'No account'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data_serializer.data,status=status.HTTP_200_OK)


class CreateQRCode(APIView):
    def post(self,request):

        data = request.data.copy()
        random_id_user = random.randint(100, 999)
        data['id_user'] = f"User{random_id_user}"
        random_id_qr = random.randint(100, 999)
        data['id_qr'] = f"Qr{random_id_qr}"


        serializer = UserInfoSerializer(data=data)

        id_AS=request.data.get('id')
        print(id_AS)
        if not id_AS: 
            return Response({'error':'AS ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            data = serializer.validated_data
            try:
                data_AS=AS.objects.get(pk=id_AS)
            except AS.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            keys_encrypt=json.loads(data_AS.encrypt_key)
            face_encode = encode_face(data['image'])
            face_encode = face_encode + "tvs"
            print(face_encode)
            
            from datetime import datetime
            current_time=datetime.now() # get time now
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            binarydata= encode_infoV2(data['id_user'],data['id_qr'],formatted_time,keys_encrypt) #encrypt AES
            
            QrCode._binarydata=binarydata
            errcorlvl = QrCode.Ecc.HIGH
            qr = QrCode.encode_text(face_encode, errcorlvl)
            imageQR=self.save_qr_image(qr)
            
            serializer.save()
            print("________________________________________________________________________________________________")
            bytes_data = bytes(int(binarydata[i:i+8], 2) for i in range(0, len(binarydata), 8))
            base64_data = base64.b64encode(bytes_data).decode('utf-8')
            data_info={
                "id_user":data['id_user'],
                "Name":data['name'],
                "DateOfBirth":data['dob'],
                "Address":data['address'],
                "PhoneNumber":data['numberPhone'],
                "Email":data['email']
            }
            print(">>>>>>>Dữ liệu cá nhân: ",data_info)
            print("________________________________________________________________________________________________")
            print(">>>>>>>Dữ liệu công khai(sinh trắc khuôn mặt): ", face_encode[:-3])
            print("________________________________________________________________________________________________")
            print(">>>>>>>Thủy vân số: ", base64_data)
            return Response({"data":imageQR},status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_304_NOT_MODIFIED)
    def generate_IdUser(self):
        number = random.randint(100, 999)  # Tạo số ngẫu nhiên có 3 chữ số
        return f"User{number}"
    def save_qr_image(self, qrcode: QrCode, scale: int = 3) -> str:
        """Generates a QR code image and returns it as a base64 string."""
        size = qrcode.get_size()
        border = 4  # Border width in "modules"
        img_size = (size + 2 * border) * scale
        img = Image.new("RGB", (img_size, img_size), "white")
        pixels = img.load()

        # Draw the QR code onto the image
        for y in range(size):
            for x in range(size):
                color = 0 if qrcode.get_module(x, y) else 255  # Black or white
                for dy in range(scale):
                    for dx in range(scale):
                        pixels[(x + border) * scale + dx, (y + border) * scale + dy] = (color, color, color)
        # Save the image to a BytesIO stream
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_base64
class RegenerateQRCode(APIView):
    def post(self,request):

        id_AS=request.data.get('id_AS')
        id_user = request.data.get('id_user')
        print(id_AS)
        print(id_user)
        if not id_AS or not id_user: 
            return Response({'error':'AS ID or User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data_AS=AS.objects.get(pk=id_AS)
            data_User = UserInfo.objects.get(pk = id_user)
        except AS.DoesNotExist or data_User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
                
            
        from .models import Hash
        Hash.objects.filter(id_qr = data_User.id_qr).delete()
        keys_encrypt=json.loads(data_AS.encrypt_key)
        face_encode = encode_face(data_User.image)
        face_encode = face_encode + "tvs"
        print(face_encode)
        random_id_qr = random.randint(100, 999)
        id_qr = f"Qr{random_id_qr}"
        from datetime import datetime
        current_time=datetime.now() # get time now
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        binarydata= encode_infoV2(id_user, id_qr,formatted_time,keys_encrypt) #encrypt AES
        
        UserInfo.objects.filter(id_user = id_user).update(id_qr = id_qr)
        QrCode._binarydata=binarydata
        errcorlvl = QrCode.Ecc.HIGH
        qr = QrCode.encode_text(face_encode, errcorlvl)
        imageQR=self.save_qr_image(qr)
            
        return Response({"data":imageQR},status=status.HTTP_200_OK)
    def save_qr_image(self, qrcode: QrCode, scale: int = 3) -> str:
        """Generates a QR code image and returns it as a base64 string."""
        size = qrcode.get_size()
        border = 4  # Border width in "modules"
        img_size = (size + 2 * border) * scale
        img = Image.new("RGB", (img_size, img_size), "white")
        pixels = img.load()

        # Draw the QR code onto the image
        for y in range(size):
            for x in range(size):
                color = 0 if qrcode.get_module(x, y) else 255  # Black or white
                for dy in range(scale):
                    for dx in range(scale):
                        pixels[(x + border) * scale + dx, (y + border) * scale + dy] = (color, color, color)
        # Save the image to a BytesIO stream
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_base64
class UserInfoHashView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserInfoSerializer(data=request.data)
        id_AS=request.data.get('id')
        if not id_AS: 
            return Response({'error':'AS ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            data = serializer.validated_data
            try:
                data_AS=AS.objects.get(pk=id_AS)
                
            except AS.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            keys_encrypt=json.loads(data_AS.encrypt_key)
            keys_Sign=json.loads(data_AS.Sign_key)

            face_encode,face_cut=encode_face(data['image'])
            data['image']=face_cut
            info_encode=encode_info(data['id_user'],data['name'],data['dob'], keys_encrypt)

            message='.'.join([face_encode,info_encode])
            sign=sign_data(message, keys_Sign)
            message='.'.join([message,sign])
            # print(data['image'])
            serializer.save()
            # img_base64 = data['image']
            # img_data = base64.b64decode(img_base64)
            # buffered = BytesIO(img_data)
            # img = Image.open(buffered)
            # img.save("recovered_face.jpg")

            return Response({"data":message},status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class createAS(APIView):
    def post(self,request):
        # them check trung ten AS cac thu
        data=request.data.copy()
        serializerAS=ASSerializer(data=data)
        if serializerAS.is_valid():
            serializerAS.save()
        else:
            return Response(serializerAS.errors,status=status.HTTP_200_OK)
        last_record=AS.objects.last()
        data['id_as']=last_record.id_as
        serializerAcc=AccountSerializer(data=data)
        if serializerAcc.is_valid():
            serializerAcc.save()
            return Response({"data":"success"},status=status.HTTP_200_OK)
        else :
            return Response(serializerAcc.errors,status=status.HTTP_200_OK)
        
class getAS(APIView):
    def post(self,request):
        id_AS=request.data.get('id_as')
        if not id_AS: 
            return Response({'error':'AS ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data=AS.objects.get(pk=id_AS)
        except AS.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        data_serializer=ASSerializer(data)
        # print(data_serializer.data)

        keys=json.loads(data.Sign_key)
        private_key=base64.b64decode(keys['private_key'])
        return Response(private_key, status=status.HTTP_200_OK)

class getAllAS(APIView):
    def get(self,request):
        try:
            data=AS.objects.all()
            data_serializer=ASSerializer(data,many=True)
        except AS.DoesNotExist:
            return Response({'error': 'No AS'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data_serializer.data,status=status.HTTP_200_OK)
class CreateAccessLog(APIView):
    def post(self,request):
        serializer = AccessLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class getAllAccessLog(APIView):
    def get(self,request):
        try:
            data=AccessLog.objects.all()
            data_serializer=AccessLogSerializer(data,many=True)
        except AccessLog.DoesNotExist:
            return Response({'error': 'No info'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data_serializer.data,status=status.HTTP_200_OK)