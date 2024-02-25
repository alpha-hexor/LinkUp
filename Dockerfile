FROM python:3.12-alpine3.18

WORKDIR /app

#copy the requirements
COPY ./requirements.txt /app/requirements.txt

#pip install
RUN pip install -r requirements.txt

#copy other stuff to the workdir
COPY app.py /app/app.py
COPY ./templates /app/templates
COPY ./avatars /app/avatars
COPY ./static /app/static

#create a database
RUN mkdir database
RUN touch database/mydatabase.db

#create a attachment
RUN mkdir attachments

#expose the port
EXPOSE 5000

#run 
CMD [ "python","app.py" ]