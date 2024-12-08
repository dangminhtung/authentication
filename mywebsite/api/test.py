def xor_encrypt_decrypt(input_file, output_file, key):
    # Chuyển key thành bytes
    key_bytes = bytearray(key, 'utf-8')
    key_len = len(key_bytes)

    with open(input_file, 'rb') as f_in:
        data = f_in.read()

    # Mã hóa/giải mã dữ liệu bằng XOR với từng byte của chuỗi key
    encrypted_data = bytearray(
        (byte ^ key_bytes[i % key_len]) for i, byte in enumerate(data)
    )

    with open(output_file, 'wb') as f_out:
        f_out.write(encrypted_data)

# Thực thi mã hóa
key = "admin1yeuem23"  # Key là một chuỗi ký tự
input_file = 'C:/Users/0818562562/Desktop/sensitive.txt'
output_file = 'C:/Users/0818562562/Desktop/sensitive_encrypted.txt'
#Thực thi giải mã
decrypted_file = 'C:/Users/0818562562/Desktop/sensitive_decrypted.txt'
xor_encrypt_decrypt(input_file, output_file, key)






