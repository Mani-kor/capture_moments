from flask import Flask, render_template, request, redirect, url_for
import boto3
import uuid
from datetime import datetime

app = Flask(__name__)

# DynamoDB connection
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')  # Replace with your region

# DynamoDB tables
photographers_table = dynamodb.Table('photographers')
bookings_table = dynamodb.Table('booking')

@app.route('/')
def home():
    return render_template('home.html', logged_in=True)

@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        form = request.form
        booking_id = str(uuid.uuid4())

        # Store booking data
        bookings_table.put_item(Item={
            'booking_id': booking_id,
            'event_type': form.get('event_type'),
            'start_date': form.get('start_date'),
            'end_date': form.get('end_date'),
            'user_name': form.get('user_name'),
            'email': form.get('email'),
            'phone': form.get('phone'),
            'package': form.get('package'),
            'photographer_id': form.get('photographer_id'),
            'payment_method': form.get('payment_method'),
            'special_requests': form.get('special_requests', ''),
            'timestamp': datetime.utcnow().isoformat()
        })

        return redirect(url_for('success'))

    # Load photographers from DynamoDB
    response = photographers_table.scan()
    photographers = response.get('Items', [])
    return render_template('book.html', photographers=photographers)

@app.route('/photographers')
def show_photographers():
    response = photographers_table.scan()
    photographers = response.get('Items', [])
    return render_template('photographers.html', photographers=photographers)

@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)
