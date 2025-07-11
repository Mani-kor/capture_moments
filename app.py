from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Add a secret key for session

photographers = [
    {"name": "John Doe", "skills": "Weddings, Portraits", "availability": "Available", "image": "john.jpg"},
    {"name": "Jane Smith", "skills": "Travel, Nature", "availability": "Available", "image": "jane.jpg"},
    {"name": "Sam Wilson", "skills": "Corporate, Product", "availability": "Booked", "image": "sam.jpg"},
    {"name": "Priya Patel", "skills": "Fashion, Editorial", "availability": "Available", "image": "priya.jpg"},
    {"name": "Alex Kim", "skills": "Sports, Action", "availability": "Booked", "image": "alex.jpg"},
    {"name": "Maria Garcia", "skills": "Food, Lifestyle", "availability": "Available", "image": "maria.jpg"}
]

@app.route('/')
def home():
    logged_in = session.get('logged_in', False)
    return render_template('home.html', logged_in=logged_in)

@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        # handle booking logic here
        return redirect(url_for('success'))
    return render_template('book.html', photographers=photographers)

@app.route('/photographers')
def photographer_page():
    return render_template('photographers.html', photographers=photographers)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Validate credentials here (add your logic)
        session['logged_in'] = True
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/services')
def services():
    services_list = [
        {"title": "Wedding Photography", "desc": "Capture your special day with beautiful, timeless photos.", "icon": "fa-heart"},
        {"title": "Birthday Parties", "desc": "Fun and candid moments from your birthday celebrations.", "icon": "fa-birthday-cake"},
        {"title": "Corporate Events", "desc": "Professional coverage for your business events and conferences.", "icon": "fa-briefcase"},
        {"title": "Product Shoots", "desc": "High-quality images to showcase your products.", "icon": "fa-camera"},
        {"title": "Family Portraits", "desc": "Cherish your family moments with creative portraits.", "icon": "fa-users"}
    ]
    return render_template('services.html', services=services_list)

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle registration logic here
        # For now, just redirect to login
        return redirect(url_for('login'))
    return render_template('sign_up.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
