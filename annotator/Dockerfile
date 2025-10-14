FROM python:3.10
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD python main.py