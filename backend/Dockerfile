FROM python:3.7-slim

WORKDIR /app

COPY backend/foodgram/requirements.txt ./

RUN python -m pip install --upgrade pip
RUN pip3 install -r requirements.txt --no-cache-dir

COPY backend/foodgram/ ./

CMD ["gunicorn", "foodgram.foodgram.wsgi:application", "--bind", "0:8000" ]
