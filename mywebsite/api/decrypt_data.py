from .models import AS
import json
import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import pyaes
import zlib
import binascii
from .models import AS
import cv2
import numpy as np
from scipy.spatial.distance import cosine
def decode_info(message):
    try:
        id=1;
        data=AS.objects.get(pk=id)
    except:
        print(KeyError)
        return False;
    keys_encrypt=json.loads(data.encrypt_key)
    face_encode, encrypted_data_base64, signature_base64=message.split('.')
    # Khóa bí mật cho AES
    aes_key = base64.b64decode(keys_encrypt['aes_key'])
    nonce = base64.b64decode(keys_encrypt['nonce'])
    cipher_aes = pyaes.AESModeOfOperationCTR(aes_key, counter=pyaes.Counter(initial_value=int.from_bytes(nonce, byteorder='big')))
    encrypted_data = base64.b64decode(encrypted_data_base64)
    decrypted_data = cipher_aes.decrypt(encrypted_data)

    info = json.loads(decrypted_data.decode('utf-8'))
    return info
def decode_infoV2(binary_data, id_as):
    try:
        data=AS.objects.get(pk = id_as)
    except:
        print(KeyError)
        return False;
    keys_encrypt=json.loads(data.encrypt_key)
    aes_key = base64.b64decode(keys_encrypt['aes_key'])
    nonce = base64.b64decode(keys_encrypt['nonce'])
    bytes_data = bytes(int(binary_data[i:i+8], 2) for i in range(0, len(binary_data), 8))
    cipher_aes = pyaes.AESModeOfOperationCTR(aes_key, counter=pyaes.Counter(initial_value=int.from_bytes(nonce, byteorder='big')))
    decrypted_data = cipher_aes.decrypt(bytes_data)
    info = json.loads(decrypted_data.decode('utf-8'))
    return info
def verify_signature(message):
    
    try:
        id=1;
        data=AS.objects.get(pk=id)
    except:
        print(KeyError)
        return False;
    keys_sign=json.loads(data.Sign_key)
    
    face_encode, info_encode, signature_base64=message.split('.')
    message='.'.join([face_encode,info_encode])
    public_key = RSA.import_key(base64.b64decode(keys_sign['public_key']))
    message_to_byte = base64.b64decode(message)
    hash_digest = SHA256.new(message_to_byte)
    signature = base64.b64decode(signature_base64)

    try:
        pkcs1_15.new(public_key).verify(hash_digest, signature)
        return True  # Chữ ký hợp lệ
    except (ValueError, TypeError):
        return False  # Chữ ký không hợp lệ
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        # Đọc ảnh dưới dạng bytes
        image_data = image_file.read()
        # Mã hóa ảnh thành base64
        encoded_image = base64.b64encode(image_data)
        # Chuyển đổi từ bytes thành chuỗi
        return encoded_image.decode('utf-8')
def base64_to_numpy(base64_str):
    # Bỏ tiền tố "data:image/jpeg;base64, => base64->byte => byte->numpy => numpy->img
    base64_str = base64_str.split(",")[1] if "," in base64_str else base64_str
    img_data = base64.b64decode(base64_str)
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img
def decompress_to_vector(compressed_base64):
    compressed_data = base64.b64decode(compressed_base64)
    vector_bytes = zlib.decompress(compressed_data)
    vector = np.frombuffer(vector_bytes, dtype=np.float64)
    return vector
def compare_vectors(vector1, vector2, threshold=0.05):
    vector1 = np.array(vector1).flatten()
    vector2 = np.array(vector2).flatten()
    distance = cosine(vector1, vector2)
    # Kiểm tra khoảng cách với ngưỡng cho phép
    print("distance = ", distance)
    return distance < threshold