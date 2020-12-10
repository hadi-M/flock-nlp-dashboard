FROM python:3.8

WORKDIR /usr/src/app
RUN apt-get update

# RUN apt-get install python3
# install python packages
RUN python -m pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt


# CMD ["cd", "./product"]
# RUN cd ./product

CMD ["python", "app.py"]