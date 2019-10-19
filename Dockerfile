FROM python:3

RUN mkdir -p /usr/src/api
WORKDIR /usr/src/api

COPY requirements.txt /usr/src/api/requirements.txt

RUN pip3 install -r requirements.txt

RUN git clone https://github.com/jesperlundqvist/Flask-CAS.git
WORKDIR /usr/src/api/Flask-CAS
RUN python3 setup.py install
WORKDIR /usr/src/api

CMD gunicorn --workers 3 --bind=0.0.0.0:5000 --chdir /usr/src api:app
