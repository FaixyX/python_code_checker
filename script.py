import requests

url = "http://127.0.0.1:8000/api/token/"
data = {
    "email": "dev@gmail.com",
    "password": "1234"
}

response = requests.post(url, data=data)

print(response.text)
# a = 1;
# b = 2;
# c = a + b;
# print(c);
