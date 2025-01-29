from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitter_clone.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    posts = db.relationship('Post', backref='user', lazy=True)  
    comments = db.relationship('Comment', backref='user', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route('/')
def home():
    if 'user_id' in session:
        posts = Post.query.order_by(Post.id.desc()).all()
        return render_template('home.html', posts=posts)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Nazwa użytkownika jest zajęta!')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Rejestracja zakończona sukcesem!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        flash('Nieprawidłowe dane logowania!')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/post', methods=['POST'])
def post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = request.form['content']
    if content:
        new_post = Post(content=content, user_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = request.form['content']
    if content:
        new_comment = Comment(content=content, post_id=post_id, user_id=session['user_id'])
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    post = Post.query.get_or_404(post_id)
    if post.user_id == session['user_id']:
        db.session.delete(post)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/delete_account')
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get_or_404(session['user_id'])
    posts = Post.query.filter_by(user_id=user.id).all()
    for post in posts:
        db.session.delete(post)
    db.session.delete(user)
    db.session.commit()
    session.clear()
    return redirect(url_for('register'))

@app.route('/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    comment = Comment.query.get_or_404(comment_id)
    
    
    if comment.user_id == session['user_id']:
        db.session.delete(comment)
        db.session.commit()
    
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)
