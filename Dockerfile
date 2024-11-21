FROM python:3.8-slim
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt
COPY . /app
EXPOSE 5000
RUN chmod +x ./run_puploader.sh
ENTRYPOINT ["sh", "run_puploader.sh"]