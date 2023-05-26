FROM python:3.7-slim

WORKDIR /app

COPY foodgram/requirements.txt ./
COPY foodgram/foodgram/settings.py ./

RUN python -m pip install --upgrade pip
RUN pip3 install -r requirements.txt --no-cache-dir

COPY . ./

CMD ["gunicorn", "foodgram.foodgram.wsgi:application", "--bind", "0:8000" ]
