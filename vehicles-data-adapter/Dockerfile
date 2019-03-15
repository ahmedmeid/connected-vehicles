FROM python:3
ADD vehicles_data_adapter.py config.json /
RUN pip install paho-mqtt requests
CMD [ "python", "./vehicles_data_adapter.py" ]
