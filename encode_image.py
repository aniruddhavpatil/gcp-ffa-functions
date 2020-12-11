import base64

f = open('./test.png', 'rb')
image = f.read()

encoded_image = base64.b64encode(image)
decoded_image = base64.b64decode(encoded_image)

o = open('./decoded.png', 'wb')
o.write(decoded_image)
print(encoded_image)