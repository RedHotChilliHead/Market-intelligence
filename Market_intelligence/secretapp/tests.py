import json

from rest_framework.test import APITestCase
from django.urls import reverse
from datetime import timedelta

from passlib.context import CryptContext
from cryptography.fernet import Fernet
from django.utils import timezone

from secretapp.models import Secret

# docker compose run secretapp python manage.py test - для правильного выполнения тестов в контейнере
# docker compose run secretapp sh -c "cd Market_intelligence && python manage.py test"
# TEST_MODE=True docker compose up -d
# docker compose exec secretapp python manage.py test
# coverage report
# docker compose exec secretapp coverage run manage.py test
# docker compose exec secretapp coverage report
# покрытие тестами 97%


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


class APIGenerateSecretTestCase(APITestCase):
    def test_generate_secret_api_view(self):
        """
        Проверка сохранения шифрованного секрета, хэшированной кодовой фразы и генерации секретного ключа
        для получения доступа к секрету
        """
        post_data = {
            "text": "It is a secret data",
            "passphrase": "Phrase",
            "TTL": 14
        }
        post_data_json = json.dumps(post_data)
        response = self.client.post(reverse('secretapp:generate'), post_data_json, content_type='application/json')

        self.assertEqual(response.status_code, 201)

        # проверяем наличие секретного ключа и ссылки в ответе
        self.assertContains(response, 'secret_key', status_code=201)
        self.assertContains(response, 'url', status_code=201)

        # проверяем корректность ссылки в ответе
        secret_key = response.data['secret_key']
        url = response.data['url']
        self.assertEqual(url, f'http://127.0.0.1:8000/secrets/{secret_key}/')

        # проверяем, что в базе данных был создан секрет
        self.assertTrue(Secret.objects.filter(secret_key=secret_key).exists())

        # проверяем, что текст секрета и кодовая фраза хранятся в зашифрованном виде
        secret = Secret.objects.get(secret_key=secret_key)
        self.assertFalse(secret.text == post_data['text'])
        self.assertFalse(secret.passphrase == post_data['passphrase'])

        # проверяем, что время жизни секрета корректно сохранилось в базе данных
        delta = timedelta(days=post_data['TTL'])
        expected_time = secret.created_at + delta
        self.assertTrue(secret.expires_at.strftime('%m/%d/%y') == expected_time.strftime('%m/%d/%y'))

        # проверяем валидацию полей
        post_data = {
            "text": "It is a secret data"
        }
        post_data_json = json.dumps(post_data)
        response = self.client.post(reverse('secretapp:generate'), post_data_json, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)  # Преобразуем контент ответа в словарь
        self.assertEqual(response_data, {'error': 'The text and the passphrase are required parameters.'})

        post_data = {
            "passphrase": "Phrase"
        }
        post_data_json = json.dumps(post_data)
        response = self.client.post(reverse('secretapp:generate'), post_data_json, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)  # Преобразуем контент ответа в словарь
        self.assertEqual(response_data, {'error': 'The text and the passphrase are required parameters.'})

        post_data = {
            "text": "It is a secret datasdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsfdsdfsdfsdfs"
                    "sdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfdddsdfsdfghfghfghfkljhsdfjklahdlkfjshfbaksdf"
                    "skhjdbfvlijksdfhiouasdhfnljkzrndh;iouhdsljfhvnkljdfhg;kljdhfgljikhdfgjk"
                    "kjsdhfjklshdfuilahyweuoiryaiwoehtjknvcbjmxvbngjl;sdhfiohdfjklcvbnjklxdfhgjklsdhgiljdfhglkjhlsjk"
                    "sdl;fksl;dfk;sldkf;lskdf;lsdk;fl",
            "passphrase": "Phrase",
        }
        post_data_json = json.dumps(post_data)
        response = self.client.post(reverse('secretapp:generate'), post_data_json, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)  # Преобразуем контент ответа в словарь
        self.assertEqual(response_data, {'error': 'The length of the secret should not exceed 300 characters, '
                                                  'and the length of the passphrase should not exceed 100'})

        post_data = {
            "passphrase": "It is a secret datasdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsfsdfsdfs"
                          "sdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfsdfdddsdfsdfghfghfghfkljhsdfjklahdlkfjshfbaksdf",
            "text": "text",
        }
        post_data_json = json.dumps(post_data)
        response = self.client.post(reverse('secretapp:generate'), post_data_json, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)  # Преобразуем контент ответа в словарь
        self.assertEqual(response_data, {'error': 'The length of the secret should not exceed 300 characters, '
                                                  'and the length of the passphrase should not exceed 100'})

        post_data = {
            "text": "It is a secret data",
            "passphrase": "Phrase",
            "TTL": 200000
        }
        post_data_json = json.dumps(post_data)
        response = self.client.post(reverse('secretapp:generate'), post_data_json, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)  # Преобразуем контент ответа в словарь
        self.assertEqual(response_data, {'error': 'The lifetime of the secret should be from 1 day to 365 days.'})


class APIOpenSecretTestCase(APITestCase):
    def setUp(self) -> None:
        self.text = 'It is a secret'
        text_encrypt = encrypt_secret(self.text)
        self.passphrase = 'Passphrase'
        passphrase_hash = hash_password(self.passphrase)
        self.secret_key = 'secret_key'
        delta = timedelta(seconds=10)
        self.secret = Secret.objects.create(text=text_encrypt,
                                            passphrase=passphrase_hash,
                                            secret_key=self.secret_key,
                                            expires_at=timezone.now() + delta)

    def tearDown(self) -> None:
        self.secret.delete()

    def test_open_secret_api_view(self):
        """
        Проверка доступа к секрету по ссылке и кодовой фразе
        """
        # проверяем отсутствие доступа к секрету, при неправильной кодовой фразе
        response = self.client.post(f'http://127.0.0.1/secrets/{self.secret_key}/',
                                    json.dumps({"passphrase": "mistake"}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'Passphrase does not match'})

        # проверяем доступ к секрету с корректными данными
        response = self.client.post(f'http://127.0.0.1/secrets/{self.secret_key}/',
                                    json.dumps({"passphrase": self.passphrase}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'secret': self.text})

        # проверяем, что секрет был удален после первого прочтения
        response = self.client.post(f'http://127.0.0.1/secrets/{self.secret_key}/',
                                    json.dumps({"passphrase": self.passphrase}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {'error': 'Secret does not exist'})

