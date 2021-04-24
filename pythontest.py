import smtplib
from email.message import EmailMessage

email = "anything@gmail.com"
password = "anything"

msg = EmailMessage()
msg['Subject'] = "Python generated mail"
msg['From'] = email
msg['To'] = email
msg.set_content('hello!')

msg.add_alternative("""\
<!DOCTYPE HTML>
<html>
    <body>
        <h1>hello welocme to EZY-BUY-SELL click the the below link to verify your email address!</h1>
        <a href="thapar.edu">verify</a>
    </body>
</html>

""", subtype="html")

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(email, password)

    smtp.send_message(msg)
