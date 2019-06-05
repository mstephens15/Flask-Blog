import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from flaskblog import mail

#Actually updates the picture, f_ext finds the extension of a pic(jpg, png)
#The _ is usually 'f_name'
#Use hex so the name of the profile pics dont overlap, which causes serious issues

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

#Resize a large photo to be 125x125. Used with the PIL(pillow) import.
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

##Sending a reset email for below route
#_external will make email have full domain
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', 
            sender='noreply@demo.com', 
            recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request, then simply ignore this email and no changes will be made.
'''
    mail.send(msg)
