from flask import Flask, request, redirect, url_for, render_template, flash
from models import db, User, Rating
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'


# Initialize database (DO NOT REINITIALIZE 'db')
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

# Ensure the 'uploads' directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Allowed extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        file = request.files['photo']

        # Check if the email already exists in the database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("A user with this email already exists. Please use a different email.", "error")
            return redirect(url_for('register'))

        # Check if the file name already exists in the database (photo_path)
        existing_photo = User.query.filter_by(photo_path='uploads/' + file.filename).first()
        if existing_photo:
            flash("A user with this photo already exists. Please upload a different photo.", "error")
            return redirect(url_for('register'))

        # Check if file is valid
        if file and allowed_file(file.filename):
            print("File is allowed")
            filename = secure_filename(file.filename)

            # Save the file to static/uploads
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(file_path)
                print(f"File saved to {file_path}")
            except Exception as e:
                print(f"Error saving file: {str(e)}")
                flash("Error uploading file. Please try again.", "error")
                return redirect(url_for('register'))

            # Save the user with the photo path
            new_user = User(email=email, photo_path='uploads/' + filename)
            db.session.add(new_user)
            db.session.commit()

            print("Registration successful")
            flash("Registration successful!", "success")
            return redirect(url_for('rate_photos'))

    return render_template('register.html')


# Route for rating photos
@app.route('/rate', methods=['GET', 'POST'])
def rate_photos():
    # Fetch two random users for voting
    users = User.query.order_by(db.func.random()).limit(2).all()

    # Fetch the leaderboard (as before)
    top_users = db.session.query(
        User, db.func.count(Rating.winner_id).label('wins')
    ).join(Rating, User.id == Rating.winner_id).group_by(User.id).order_by(db.func.count(Rating.winner_id).desc()).limit(3).all()

    if len(users) < 2:
        flash("Not enough users to rate. Please register more users.", "error")
        return redirect(url_for('register'))

    user1, user2 = users

    if request.method == 'POST':
        choice = request.form['choice']  # Retrieve the user's choice ('left' or 'right')
        user1_id = request.form['user1_id']
        user2_id = request.form['user2_id']

        # Determine the winner and loser based on the choice
        if choice == 'left':
            winner_id, loser_id = user1_id, user2_id
        else:
            winner_id, loser_id = user2_id, user1_id

        # Record the vote in the Rating table
        rating = Rating(winner_id=winner_id, loser_id=loser_id)
        db.session.add(rating)
        db.session.commit()

        flash("Thank you for voting!", "success")
        return redirect(url_for('rate_photos'))

    return render_template('rate.html', user1=user1, user2=user2, top_users=top_users)




@app.route('/leaderboard')
def leaderboard():
    # Fetch the top 3 users with the most wins
    top_users = db.session.query(
        User, db.func.count(Rating.winner_id).label('wins')
    ).join(Rating, User.id == Rating.winner_id).group_by(User.id).order_by(db.func.count(Rating.winner_id).desc()).limit(3).all()

    return render_template('leaderboard.html', top_users=top_users)




# Main route (optional)
@app.route('/')
def index():
    return redirect(url_for('register'))

# Privacy policy route
@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

# Terms of use route
@app.route('/terms_of_use')
def terms_of_use():
    return render_template('terms_of_use.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)