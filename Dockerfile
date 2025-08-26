FROM python:3.10.18

WORKDIR /app

RUN apt-get update -y && apt-get install -y git unixodbc-dev

RUN git clone https://github.com/Lalith-SSIT/C360.git .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p logs outputs data/temp

EXPOSE 8000 8501

CMD ["python", "app.py"]