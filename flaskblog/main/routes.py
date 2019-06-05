from flask import render_template, request, Blueprint
from flaskblog.models import Post

main = Blueprint('main', __name__)



@main.route("/")
@main.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
#Shows first _ posts on the home page, starting with the newest due to 'post.date_posted.desc()'    
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=4)
    return render_template('home.html', posts=posts)

@main.route("/about")
def about():
    return render_template('about.html', title='About')