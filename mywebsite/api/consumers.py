import json
from channels.generic.websocket import AsyncWebsocketConsumer
from PIL import Image
import base64
from pyzbar.pyzbar import decode
from asgiref.sync import async_to_sync
from .models import AS, UserInfo
from .serializers import UserInfoSerializer
import cv2
import numpy as np
import threading
import requests
from .decrypt_data import decode_info,verify_signature,decompress_to_vector,compare_vectors, decode_infoV2
import face_recognition
import time
from django.conf import settings
from .models import AccessLog
import subprocess

class ScanQR_and_Face(AsyncWebsocketConsumer):
    _idUser: str
    _idAS : str
    async def connect(self):
        await self.accept()

        # Bắt đầu quét QR code trong một luồng riêng biệt
        print("mo socket")


    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('action') == 'start_face_scan':
            scan_face_thread=threading.Thread(target=self.start_face_scan)
            scan_face_thread.start()
        if data.get('action')=='start_qr_scan':
            print("Start QR Scan: ")

            self._idAS = data.get('id_as')
            
            scan_thread = threading.Thread(target=self.capture_and_scan_qr)
            scan_thread.start()
    def read_qr_with_java(self):
        try:
            class_directory = "C:/Users/minhtung/Documents/NetBeansProjects/JavaApplication1/build/classes"
            class_name = "javaapplication1.JavaApplication1"
            command = [
                "java",
                "-cp", f".;C:/Users/minhtung/Desktop/zxing-zxing-3.5.3/zxing-zxing-3.5.3/core/target/core-3.5.3.jar;C:/Users/minhtung/Desktop/jar_files/javase-3.5.3.jar",
                class_name,
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=class_directory)
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            return None
    def convert_negatives_to_positives(self,decimal_int):
        for i in range(len(decimal_int)):
            if decimal_int[i] < 0:
                k = 8
                decimal_int[i] = (1 << k) + decimal_int[i]
        return decimal_int

    def TachKetQua(self,input_string):
        result=""
        int_arrays = []
        string_parts= input_string.strip().split("#")
        for i in range(len(string_parts)):
            if string_parts[i][1]=="R":
                result=string_parts[i][2:]
            else:
                int_array = list(map(int, string_parts[i].strip().split()))
                int_array = self.convert_negatives_to_positives(int_array)
                int_arrays.append(int_array)
        return int_arrays,result
    def changeBitStr(self,s):
        if s=="0": return "1"
        else: return "0"
    def extractLen(self,_arrayLen):
        binary_len=""
        for i in range(0,10,2):
            binary=format(_arrayLen[i],'08b')
            if binary[6]=="0":
                binary_len = binary_len + binary[4] + binary[2]
            else :
                binary_len = binary_len + self.changeBitStr(binary[4]) + self.changeBitStr(binary[2])
        return binary_len
    def extractData(self,_arrayData,numEmbedData):
        binary_data=""
        for i in range(0,numEmbedData,2):
            # print(_arrayData[i])
            binary = format(_arrayData[i],'08b')
            if binary[6]=="0":
                binary_data = binary_data + binary[4] + binary[2]
            else :
                binary_data = binary_data + self.changeBitStr(binary[4]) + self.changeBitStr(binary[2])
        return binary_data
    def capture_and_scan_qr(self):
        print(self._idAS)
        input_string = self.read_qr_with_java()
        if input_string is not None:
            int_arrays,result_face=self.TachKetQua(input_string)
            mark = result_face[-3:]
            result = result_face[:-3]
            if(len(int_arrays) < 56 or mark != "tvs"):
                extra_data = {
                    'tvs':'null'
                }
                serialized_data= json.dumps(extra_data)
                self.send_qr_data(serialized_data) 
                return
            self.scope['session']['face_encode'] = result

            print(result)
            # self.scope['session']['info_encode']=json.dumps(info)
            self.scope['session'].save()
            _arrayLen=int_arrays[0][int_arrays[0][0]+1:]
            binary_len=self.extractLen(_arrayLen)
            Secret_len = int(binary_len, 2)
            numEmbedData = Secret_len / (len(int_arrays)-1)
            if(int(numEmbedData) % 2 == 0 ):
                if(numEmbedData % 2 !=0 ) : numEmbedData = int(numEmbedData) + 2
                else : numEmbedData = int(numEmbedData)
            else:
                numEmbedData = int(numEmbedData) + 1
            # tinh so khoi duoc nhung
            numChunks = Secret_len // numEmbedData
            # trich xuat du lieu
            EmbedData=""
            for i in range(1,numChunks + 1):
                # print(">>>>>>>>>Block>>>", i)
                _arrayData=int_arrays[i][int_arrays[i][0]+1:]
                binary_data = self.extractData(_arrayData, numEmbedData)
                EmbedData = EmbedData + binary_data
            if (Secret_len / numEmbedData) > numChunks:
                print(Secret_len - (numChunks*numEmbedData))
                _arrayData=int_arrays[numChunks + 1][int_arrays[numChunks + 1][0]+1:]
                EmbedData = EmbedData + self.extractData(_arrayData, Secret_len - (numChunks*numEmbedData))
            
            import hashlib
            bytes_data = bytes(int(EmbedData[i:i+8], 2) for i in range(0, len(EmbedData), 8))
            hash_object=hashlib.sha256(bytes_data)
            hash_hex=hash_object.hexdigest()
            from .models import Hash
            hash_values = Hash.objects.filter(value_hash=hash_hex)
            
            if hash_values.exists():
                print("ma QR hop le")
                hash_value = hash_values.first()

                data_decrypt=decode_infoV2(EmbedData, self._idAS)
                print(data_decrypt['id_user'])
                
                self._idUser = data_decrypt['id_user']
                user_info = UserInfo.objects.get(id_user=data_decrypt['id_user']) 
                user_serializer = UserInfoSerializer(user_info)
                serialized_data = user_serializer.data
                
                base64_data = base64.b64encode(bytes_data).decode('utf-8')
                extra_data = {
                    'tvs':base64_data,
                    'dataQR':serialized_data
                }
                serialized_data= json.dumps(extra_data)
                self.send_qr_data(serialized_data)    
            else :
                print("ma QR khong hop le")
                base64_data = base64.b64encode(bytes_data).decode('utf-8')
                extra_data = {
                    'tvs':base64_data
                }
                serialized_data= json.dumps(extra_data)
                self.send_qr_data(serialized_data) 
    def send_qr_data(self, qr_data):
        async_to_sync(self.send)(text_data=json.dumps({
            'type':'qr_result',
            'data': qr_data
        }))
    def start_face_scan(self):
        print("start face scan: ")
        ip_webcam_url=settings.IP_WEBCAM_URL
        face_encode=self.scope['session'].get('face_encode')

        user_info = UserInfo.objects.get(id_user=self._idUser)
        current_embedding=decompress_to_vector(face_encode)
        start_time=time.perf_counter()
        a=0
        dissimilar=0
        similar=0;
        while(True):
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time > 20:
                break
            a=a+1
            print(a)
            response=requests.get(ip_webcam_url)
            img_arr = np.array(bytearray(response.content), dtype=np.uint8)
            image = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if image is not None:
                face_location=face_recognition.face_locations(image)
                if(face_location):
                    face_encodings = face_recognition.face_encodings(image, known_face_locations=face_location)
                    is_match = compare_vectors(current_embedding, face_encodings)
                    if is_match:
                        self.send_face_result('yes')
                        similar=1
                        print("khuon mat da duoc xac thuc")

                        AccessLog.objects.create(id_user=user_info,name=user_info.name,dob=user_info.dob,status="Success")
                        break;
                    else:
                        print("khuon mat khong khop")
                        dissimilar=1
                else :
                    print("chua tim thay khuon mat")
            time.sleep(0.5)        
        print("da thoat khoi vong while")
        if dissimilar==1 and similar==0:
            print("khuon mat khong khop, xin vui long thu lai")
            self.send_face_result('false')
            AccessLog.objects.create(id_user=user_info,name=user_info.name,dob=user_info.dob,status="Failed")
        if dissimilar==0 and similar==0:
            print("qua thoi gian xac thuc")
            self.send_face_result('overtime')
            AccessLog.objects.create(id_user=user_info,name=user_info.name,dob=user_info.dob,status="Overtime")
        # print(self.scope['session'].keys())
        # del self.scope['session']['face_encode']
        # self.scope['session'].save()
        # pass

    def send_face_result(self, face_result):
        async_to_sync(self.send)(text_data=json.dumps({
            'type':'face_result',
            'data': face_result
        }))

    async def disconnect(self,close_code):
        pass
class Scantest(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # Bắt đầu quét QR code trong một luồng riêng biệt
        print("mo socket")
        scan_thread = threading.Thread(target=self.capture_and_scan_qr)
        scan_thread.start()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('action') == 'start_face_scan':
            scan_face_thread=threading.Thread(target=self.start_face_scan)
            scan_face_thread.start()
        if data.get('action')=='start_qr_scan':
            print("quet qr lan 2 ")
            scan_thread = threading.Thread(target=self.capture_and_scan_qr)
            scan_thread.start()
    def capture_and_scan_qr(self):
        print("Start QR Scan: ")
        ip_webcam_url=settings.IP_WEBCAM_URL
        
        while True:
            response=requests.get(ip_webcam_url)
            img_arr = np.array(bytearray(response.content), dtype=np.uint8)
            image = cv2.imdecode(img_arr, -1)
            if image is not None:
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                decoded_objects = decode(pil_image)
                qr_code = [obj.data.decode('utf-8') for obj in decoded_objects]
                if qr_code:
                    print("Found QR code:", qr_code)
                    message=qr_code[0];
                    check=verify_signature(message)
                    if check :
                        info=decode_info(message)

                        face_encode, info_encode, sign=message.split('.')
                        self.scope['session']['face_encode']=face_encode
                        self.scope['session']['info_encode']=json.dumps(info)
                        self.scope['session'].save()
                    else:
                        info="khong xac dinh duoc ma QR"
                    self.send_qr_data(info)
                    break;
    def send_qr_data(self, qr_data):
        async_to_sync(self.send)(text_data=json.dumps({
            'type':'qr_result',
            'data': qr_data
        }))
    def start_face_scan(self):
        print("start face scan: ")
        ip_webcam_url=settings.IP_WEBCAM_URL
        face_encode=self.scope['session'].get('face_encode');
        info_encode= json.loads(self.scope['session'].get('info_encode'))
        user_info = UserInfo.objects.get(id_user=info_encode['id_user']) 
        current_embedding=decompress_to_vector(face_encode)
        start_time=time.perf_counter()
        a=0
        dissimilar=0
        similar=0;
        while(True):
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time > 15:
                break
            a=a+1
            print(a)
            response=requests.get(ip_webcam_url)
            img_arr = np.array(bytearray(response.content), dtype=np.uint8)
            image = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if image is not None:
                face_location=face_recognition.face_locations(image)
                if(face_location):
                    face_encodings = face_recognition.face_encodings(image, known_face_locations=face_location)
                    is_match = compare_vectors(current_embedding, face_encodings)
                    if is_match:
                        self.send_face_result('yes')
                        similar=1
                        print("khuon mat da duoc xac thuc")

                        AccessLog.objects.create(id_user=user_info,name=info_encode['name'],dob=info_encode['dob'],status="Success")
                        break;
                    else:
                        print("khuon mat khong khop")
                        dissimilar=1
                else :
                    print("chua tim thay khuon mat")
            time.sleep(0.5)        
        print("da thoat khoi vong while")
        if dissimilar==1 and similar==0:
            print("khuon mat khong khop, xin vui long thu lai")
            self.send_face_result('false')
            AccessLog.objects.create(id_user=user_info,name=info_encode['name'],dob=info_encode['dob'],status="Failed")
        if dissimilar==0 and similar==0:
            print("qua thoi gian xac thuc")
            self.send_face_result('overtime')
            AccessLog.objects.create(id_user=user_info,name=info_encode['name'],dob=info_encode['dob'],status="Overtime")
        # print(self.scope['session'].keys())
        # del self.scope['session']['face_encode']
        # self.scope['session'].save()
        # pass

    def send_face_result(self, face_result):
        async_to_sync(self.send)(text_data=json.dumps({
            'type':'face_result',
            'data': face_result
        }))

    async def disconnect(self,close_code):
        pass
