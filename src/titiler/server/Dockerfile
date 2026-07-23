FROM python:3.13

WORKDIR /app

COPY main.py requirements.txt .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
