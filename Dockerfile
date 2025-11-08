FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app
COPY . .

# uploads dir
RUN mkdir -p /app/uploads

EXPOSE 5000

# start app (bind to 0.0.0.0 so it's reachable desde fuera del contenedor)
CMD ["python", "app.py"]