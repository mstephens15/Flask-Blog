import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                            PostForm, RequestResetForm, ResetPasswordForm)
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
#Shows first _ posts on the home page, starting with the newest due to 'post.date_posted.desc()'    
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=4)
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')

#Gets registration form from forms.py
#f string used because it passes data
#.data just comes from what is put into the box (i.e. someone's email)

@app.route("/register", methods=['GET', 'POST'])
def register():

#if user is logged in , clicking on Register will redirect to home page    
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
#Actually creates an account for the user on the database
    #Protects their password by hashing it
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
    #Creates the user, adds them to database based on their data, by committing it
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
    #Flash is just a popup message, doesnt actually make account
    #'your account has been created...' = message, 'success' = category
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


### Login
#first, sees if user is the same as any user in the database
#then, runs another condition to see if that is true and the password is right
#if that is true, then log them in and return home

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

###Logout

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

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

###All of this code appears only when someone logs in

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()

#This is when you actually change your username or password or picture, it will update the data.
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))

#Shows current username and email in the fields when you go to account preferences        
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

#this is equal to the file the user uploads, stored in the database(or default if they have none)
#it is getting the url for the foler where the profile pics are stored, in the 'static/profile_pics/' route
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

###Create a new post
#form = form passes the PostForm, now named form, to the template. Now, the template can actually be shown

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():

#Saves the post to the database, and is shared on the actual page
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

###Allows you to go to a specific post. <post_id> changes depending on which post you click on.
#Since we expect post_id to be an integer, we include int

@app.route('/post/<int:post_id>')
def post(post_id):
    
#Sees if the post is there. get_or_404 gets the post, or returns 404 error
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

###Allows you to update the post after it has been posted
@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)

  #Checks if current user is the one who wrote the post we are looking at
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))

#Populates the form, so the old title and content appear when you are updating it.  
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

###For deleting a post
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

###For showing all of the posts for one user
@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

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

###For entering email, where new password will be sent
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:   #Checks if they are logged in
        return redirect(url_for('home'))
    form = RequestResetForm()

  #When they enter correct email  
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

###When they get a token from an email, they come here to validate it
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to login', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
    