# Базовий образ з Python
FROM python:3.12

# Робоча директорія в контейнері
WORKDIR /app

# Копіюємо залежності
COPY requirements.txt .

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо увесь проєкт
COPY . .

# Відкриваємо порт
EXPOSE 8000

# Запуск gunicorn сервера
CMD ["gunicorn", "LEARNING.wsgi:application", "--bind", "0.0.0.0:8000"]
