import face_recognition
import base64
import numpy as np
import zlib
import cv2
import json
import os 
import pyaes
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from io import BytesIO
from PIL import Image



def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        encoded_image = base64.b64encode(image_data)
        # Chuyển đổi từ bytes thành chuỗi
        return encoded_image.decode('utf-8')
    
def compress_vector(vector):
    # Chuyển đổi vector thành chuỗi byte với kiểu dữ liệu gốc
    vector_bytes = np.array(vector, dtype=np.float64).tobytes()
    # Nén dữ liệu bằng zlib
    compressed_data = zlib.compress(vector_bytes)
    # Chuyển đổi dữ liệu nén sang base64 để dễ dàng truyền tải
    compressed_base64 = base64.b64encode(compressed_data).decode('utf-8')
    return compressed_base64
def base64_to_numpy(base64_str):
    # Bỏ tiền tố "data:image/jpeg;base64, => base64->byte => byte->numpy => numpy->img
    base64_str = base64_str.split(",")[1] if "," in base64_str else base64_str
    img_data = base64.b64decode(base64_str)
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img
def createKeyAES(salt,password):
    iterations = 100000
    aes_key=PBKDF2(password, salt, dkLen=32, count=iterations)
    return aes_key;

# _______encrypt____________________________________________________________________________________________________
def  encode_face(base64_image):
    image_np=base64_to_numpy(base64_image)
    face_locations = face_recognition.face_locations(image_np)

    # Hiển thị kết quả
    print(f"Đã phát hiện {len(face_locations)} khuôn mặt(s)")
    for face_location in face_locations:
        top, right, bottom, left = face_location
        print(f"Khuôn mặt tại vị trí: Top: {top}, Right: {right}, Bottom: {bottom}, Left: {left}")
        face_image = image_np[top:bottom, left:right]
        face_image_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(face_image_rgb)
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG") 

        
    # img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    face_encodings=face_recognition.face_encodings(image_np,face_locations)
    compressed_vector = compress_vector(face_encodings)


    return compressed_vector
def encode_info(id_user,name,dob,keys_encrypt):
    info={
        "id_user":id_user,
        "name":name,
        "dob":dob
    }
    info_str = json.dumps(info)
    # Khóa bí mật cho AES
    aes_key = base64.b64decode(keys_encrypt['aes_key'])
    nonce = base64.b64decode(keys_encrypt['nonce'])
    cipher_aes = pyaes.AESModeOfOperationCTR(aes_key, counter=pyaes.Counter(initial_value=int.from_bytes(nonce, byteorder='big')))
    encrypted_data = cipher_aes.encrypt(info_str.encode('utf-8'))
    encrypted_data_base64 = base64.b64encode(encrypted_data).decode('utf-8')

    return encrypted_data_base64
def encode_infoV2(id_user,id_qr,time_stamp,keys_encrypt):
    info={
        "id_user":id_user,
        "time_stamp":time_stamp
    }
    info_str = json.dumps(info)
    aes_key = base64.b64decode(keys_encrypt['aes_key'])
    nonce = base64.b64decode(keys_encrypt['nonce'])
    cipher_aes = pyaes.AESModeOfOperationCTR(aes_key, counter=pyaes.Counter(initial_value=int.from_bytes(nonce, byteorder='big')))
    encrypted_data = cipher_aes.encrypt(info_str.encode('utf-8'))

    import hashlib
    hash_object=hashlib.sha256(encrypted_data)
    hash_hex=hash_object.hexdigest()
    from .models import Hash
    Hash.objects.create(value_hash=hash_hex,id_qr= id_qr)
    # print(hash_hex)


    binary_data = ''.join(format(byte, '08b') for byte in encrypted_data)
    return binary_data
def sign_data(message, keys_sign):
    #cặp khóa RSA   
    private_key =  base64.b64decode(keys_sign['private_key'])
    public_key =  base64.b64decode(keys_sign['public_key'])
    message_to_byte=base64.b64decode(message)
    hash_digest = SHA256.new(message_to_byte)
    signature = pkcs1_15.new(RSA.import_key(private_key)).sign(hash_digest)
    signature_base64 = base64.b64encode(signature).decode('utf-8')
    return signature_base64

# ___create Key____________________________________________________________________________________________________
def generateKeyEncrypted():
    salt=os.urandom(16)
    nonce=os.urandom(16)
    password = b"my_secure_password"
    iterations = 100000
    aes_key=PBKDF2(password, salt, dkLen=32, count=iterations)
    return {
        'aes_key':base64.b64encode(aes_key).decode('utf-8'),
        'nonce':base64.b64encode(nonce).decode('utf-8')
    }
def generateKeySign():
    key=RSA.generate(2048)
    private_key=key.export_key()
    public_key=key.publickey().export_key()
    return {
        'private_key':base64.b64encode(private_key).decode('utf-8'),
        'public_key':base64.b64encode(public_key).decode('utf-8')
    };

    