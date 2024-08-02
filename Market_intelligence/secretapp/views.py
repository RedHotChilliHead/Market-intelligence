import random

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from passlib.context import CryptContext
from cryptography.fernet import Fernet

from secretapp.models import Secret

from datetime import timedelta
from django.utils import timezone

# функции хеширования кодовой фразы
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# хэширование кодовой фразы
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# верификация кодовой фразы
def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


# Генерация ключа
# key = Fernet.generate_key()

# ключ для шифрования и расшифровки (временный вариант)
SECRET_KEY = b'PzyzwnjqsaSAFvFuLEVvT1Sr-YUbFERx-5LIvWB8t3w='
cipher_suite = Fernet(SECRET_KEY)


# шифрование секрета
def encrypt_secret(secret: str) -> str:
    return cipher_suite.encrypt(secret.encode()).decode()


# расшифровка секрета
def decrypt_secret(encrypted_secret: str) -> str:
    return cipher_suite.decrypt(encrypted_secret.encode()).decode()


class GenerateAPIView(APIView):
    """
    This application is designed to create one-time secrets.
    The API method accepts a secret (in the form of text) and a passphrase,
    which can be used later to access the secret.
    The method returns the secret key and the url where you can go and enter the passphrase and open the secret.
    The secret key is part of the url.
    The secret lifetime (TTL) is an optional parameter, it must take values from 1 to 365 days (in days).
    Example of a POST request: /generate/
    {"text":"It is a secret data", "passphrase":"Phrase", "TTL": 7}
    """

    def post(self, request: Request) -> Response:

        try:
            text = request.data['text']
            passphrase = request.data['passphrase']
        except KeyError:
            return Response({'error': 'The text and the passphrase are required parameters.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if len(text) > 300 or len(passphrase) > 100:
            return Response({'error': 'The length of the secret should not exceed 300 characters, '
                                      'and the length of the passphrase should not exceed 100'},
                            status=status.HTTP_400_BAD_REQUEST)
        secret_key = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(32))

        passphrase_hash = hash_password(passphrase)  # хэшируем кодовую фразу
        text_encrypt = encrypt_secret(text)

        try:
            delta_str = request.data['TTL']
            delta_int = int(delta_str)
            if delta_int < 1 or delta_int > 365:
                raise ValueError
            delta = timedelta(days=delta_int)
        except ValueError:
            return Response({'error': 'The lifetime of the secret should be from 1 day to 365 days.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            delta = timedelta(days=7)

        Secret.objects.create(text=text_encrypt,
                              passphrase=passphrase_hash,
                              secret_key=secret_key,
                              expires_at=timezone.now() + delta)

        return Response({"secret_key": secret_key,
                         'url': f'http://127.0.0.1:8000/secrets/{secret_key}/'}, status=status.HTTP_201_CREATED)


class SecretAPIView(APIView):
    """
    The API method accepts a passphrase, and returns the secret.
    The secret key is part of the url.
    After reading, the secret is deleted.
    Example of a POST request: /secrets/10j6cdagu1t5ves2fyfdcq8fq77b9ebk/
    {"passphrase":"Phrase"}
    """

    def post(self, request: Request, secret_key) -> Response:
        passphrase = request.data['passphrase']
        try:
            secret = Secret.objects.get(secret_key=secret_key)
        except Secret.DoesNotExist:
            return Response({'error': 'Secret does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if verify_password(passphrase, secret.passphrase):  # верифицируем кодовую фразу с хэшем
            text = secret.text
            decrypt_text = decrypt_secret(text)
            secret.delete()
            return Response({"secret": decrypt_text}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Passphrase does not match'}, status=status.HTTP_400_BAD_REQUEST)
