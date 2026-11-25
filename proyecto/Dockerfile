# Imagen base Python 3.12 ligera preparada para desacoplamiento en Microservicios (Semana 14)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir \
    Django>=5.1,<5.3 \
    djangorestframework>=3.15.0 \
    django-cors-headers>=4.4.0 \
    drf-spectacular>=0.27.0 \
    django-filter>=24.0 \
    PyYAML>=6.0.1

COPY . .

RUN python manage.py migrate --noinput && python poblar_datos.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/')" || exit 1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
