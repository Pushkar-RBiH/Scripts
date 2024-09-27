with open('C:\Users\rbih2\Downloads\nsdl_cert.pfx', 'rb') as file:
    blob_data = file.read().hex()

print(blob_data)
