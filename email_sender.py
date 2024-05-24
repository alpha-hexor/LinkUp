from email.message import EmailMessage
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

with open('creds.json','r') as f:
    data = json.load(f)

email_sender = data['email']
password = data['password']


subject = "Linkup Verification code"

def send_email(receive_email:str,otp:str)->None:
    html = f"""
    <html>
    <body>
        <p>Hi,<br>
        This is your 6 digit linkup verfication code <h1>{otp}</h1>
        </p>
    </body>
    </html>
    """

    em = MIMEMultipart("alternative")
    em['From'] = email_sender
    em['To'] = receive_email
    em['Subject'] = subject
    html_body = MIMEText(html, "html")
    em.attach(html_body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
        smtp.login(user=email_sender,password=password)
        smtp.sendmail(from_addr=email_sender,to_addrs=receive_email,msg=em.as_string())
