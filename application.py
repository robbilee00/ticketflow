from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import init_db, User, Ticket, Comment, Attachment, db
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup
import psycopg2
import os
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

application = Flask(__name__)

application.secret_key = '*****''
s3 = boto3.client('s3')
bucket_name = '*****'


# Configure database URI with username and password
db_username = 'postgres'
db_password = '******'
db_host = 'awseb-e-hbhqxacb4r-stack-awsebrdsdatabase-24hmrn6pm6tl.c9swseukmyjc.us-east-2.rds.amazonaws.com'
application.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_username}:{db_password}@{db_host}'
init_db(application)

@application.route("/")
def main():
    if 'email' in session:
        user_id = session['email']
        user_info = get_user_info(user_id)
        if user_info is not None:
            user_name = user_info.get('username')
        else:
            user_name = "Unknown"


        users = User.query.all()
        tickets = Ticket.query.all()
        comments = Comment.query.all()
        attachments = Attachment.query.all()

        #DEBUG TOOLKIT:
        # Print users table
        # print("Users:")
        # for user in users:
        #     print(f"ID: {user.id}, Email: {user.email}, Username: {user.username}")
        
        # Print tickets table
        # print("\nTickets:")
        # for ticket in tickets:
        #     description = ticket.description[:200] if len(ticket.description) > 200 else ticket.description
        #     print(f"ID: {ticket.id}, Ticket Number: {ticket.ticket_number}, Description: {description}, Status: {ticket.status}, Assignee: {ticket.assignee}, Raised By: {ticket.raised_by}, Created On: {ticket.created_on.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print comments table
        # print("Comments:")
        # for comment in comments:
        #     print(f"ID: {comment.id}, Ticket ID: {comment.ticket_id}, Message: {comment.message}, Username: {comment.username}, Assignee: {ticket.assignee}, Created On: {comment.created_on.strftime('%Y-%m-%d %H:%M:%S')}")
        # #print_tickets_table_schema()


       # Convert User instances to dictionaries
        users_data = [{'id': user.id, 'email': user.email, 'username': user.username} for user in users]

        # Convert Ticket instances to dictionaries
        tickets_data = [{'id': ticket.id, 'ticket_number': ticket.ticket_number, 'description': ticket.description[:200] + '...' if len(ticket.description) > 200 else ticket.description, 
                        'assignee': ticket.assignee, 'status': ticket.status, 'raised_by': ticket.raised_by, 'created_on': str(ticket.created_on)} 
                        for ticket in tickets]

        # Convert Comment instances to dictionaries
        comments_data = [{'id': comment.id, 'message': comment.message, 'created_on': comment.created_on, 
                        'username': comment.username, 'ticket_id': comment.ticket_id} 
                        for comment in comments]

        # Convert Attachment instances to dictionaries
        attachments_data = [{'id': attachment.id, 'url': attachment.url, 'created_on': attachment.created_on, 
                            'username': attachment.username, 'ticket_id': attachment.ticket_id} 
                            for attachment in attachments]

        return render_template('main.html', user_name=user_name, users=users_data, tickets=tickets_data, comments_data=comments_data, attachments_data=attachments_data)
    return redirect(url_for('login'))

@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Query the User table for a user with the provided email
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            # If the user exists and the password is correct, set the user's email in the session
            session['email'] = user.email
            return redirect(url_for('main'))
        else:
            # If authentication fails, render the login template with an error message
            return render_template('login.html', error='Invalid email or password')

    # Render the login template for GET requests
    return render_template('login.html')

@application.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

@application.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

         # Check if the user already exists in the database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            message = "User with this email already exists. Please use a different email."
            return render_template("registration.html", message=message)

        # Create a new User object with the provided data
        new_user = User(email=email, username=username, password=hashed_password)

        try:
            # Add the new user to the database session
            db.session.add(new_user)
            db.session.commit()
            # Redirect to the login page after successful registration
            return redirect(url_for('login'))
        except Exception as e:
            error_message = str(e)
            return render_template("registration.html", message=error_message)

    # Render the registration form template for GET requests
    return render_template("registration.html")


def get_user_info(user_id):
    try:
        # Query the User table for a user with the provided email
        user = User.query.filter_by(email=user_id).first()
        
        if user:
            # If the user exists, return a dictionary containing user information
            user_info = {
                'id': user.id,
                'email': user.email,
                'username': user.username,
            }
            return user_info
        else:
            # If user is not found, return None
            return None
    except Exception as e:
        # Handle any database error
        print("Error fetching user information:", e)
        return None

    
# Function to create a new ticket
def create_ticket(ticket):
    try:
        # Create a new Ticket object with the provided data
        new_ticket = Ticket(
            ticket_number=ticket.ticket_number,
            description=ticket.description,
            status=ticket.status,
            assignee=ticket.assignee,
            raised_by=ticket.raised_by,
            created_on=ticket.created_on
        )

        # Add the new ticket to the database session
        db.session.add(new_ticket)

        # Commit the transaction to save the ticket to the database
        db.session.commit()

        return True
    except Exception as e:
        # Rollback the transaction if an error occurs
        print("Error creating ticket:", e)
        db.session.rollback()
        return False

# Function to update a ticket with new comments and attachments
def update_ticket(ticket_number, description, assignee, status, created_on, new_comment_text, new_attachment_url, username):
    try:
        # Retrieve the ticket object from the database
        ticket = Ticket.query.filter_by(ticket_number=ticket_number).first()

        if ticket:
            # Update ticket information
            ticket.description = description
            ticket.assignee = assignee
            ticket.status = status
            ticket.created_on = created_on

            # Check if a new comment is provided
            if new_comment_text:
                # Create a new comment object and add it to the ticket
                new_comment = Comment(message=new_comment_text, username=username, created_on=created_on)
                ticket.comments.append(new_comment)
                print("Comment added")

            # Check if a new attachment is provided
            if new_attachment_url:
                # Create a new attachment object and add it to the ticket
                new_attachment = Attachment(url=new_attachment_url, username=username, created_on=created_on)
                ticket.attachments.append(new_attachment)
                print("Attachment added")

            # Commit changes to the database
            db.session.commit()
            return True
        else:
            return False  # Ticket not found
    except IntegrityError as e:
        print("Error updating ticket:", e)
        db.session.rollback()
        return "Failed to update ticket due to database integrity error. Is the ticket in the database?"
    except Exception as e:
        print("Error updating ticket:", e)
        db.session.rollback()
        return False

    
@application.route('/new_ticket')
def new_ticket():
    if 'email' in session:
        user_id = session['email']
        user = User.query.filter_by(email=user_id).first()
        if user:
            user_name = user.username
        else:
            user_name = "Unknown"

        # Fetch the list of users from the database
        users = User.query.with_entities(User.username).all()
        users = [row[0] for row in users]

        return render_template('newticket.html', user_name=user_name, users=users)
    return redirect(url_for('login'))

@application.route('/create_ticket', methods=['POST'])
def handle_create_ticket():
    if request.method == 'POST':
        ticket_number = generate_ticket_number()
        description = request.form['description'] if 'description' in request.form else 'No Description'
        status = "new"
        assignee = request.form['assignee'] if 'assignee' in request.form else 'Unassigned'
        raised_by = session['email'] if 'email' in session else 'Unknown'
        created_on = str(datetime.now())

        ticket = Ticket(ticket_number=ticket_number, description=description, status=status, assignee=assignee, raised_by=raised_by, created_on=created_on)

        try:
            db.session.add(ticket)
            db.session.commit()
            return redirect(url_for('main'))
        except Exception as e:
            print("Error creating ticket:", e)
            return "Failed to create ticket. Please try again later."

@application.route('/update_ticket', methods=['POST'])
def handle_update_ticket():
    message = ""
    attachment_file = ""
    attachment_path = ""
    if request.method == 'POST':
        ticket_number = request.form['ticket_number']
        description = request.form['description'] if 'description' in request.form else 'No Description'
        assignee = request.form['assignee'] if 'assignee' in request.form else 'Unassigned'
        status = request.form['status'] if 'status' in request.form else 'new'
        created_on = datetime.now()
        new_comment_text = request.form['comment']
        # Check if file was uploaded
        if 'attachment' in request.files:
            attachment_file = request.files['attachment']
            if attachment_file.filename != '':
                # Secure the filename
                filename = secure_filename(attachment_file.filename)
                # Save the file to a temporary location
                upload_folder = 'uploads'
                os.makedirs(upload_folder, exist_ok=True)
                attachment_path = os.path.join(upload_folder, filename)
                attachment_file.save(attachment_path)
                new_attachment_url = attachment_path
            else:
                new_attachment_url = None
                print("attachment has no filename")
        else:
            new_attachment_url = None
            print("No attachments found")

        print( "Ticket Number: ", ticket_number, "\nDescription: Intentionally removed", "\nAssignee: ", assignee, "\nCreated On: ", created_on,"\nNew Comments: ", new_comment_text, "\nAttachemts: ", new_attachment_url)

        user = User.query.filter_by(email=session.get('email')).first()
        if user:
            username = user.username
        else:
            return "User information not found. Please log in again."

        ticket = Ticket.query.filter_by(ticket_number=ticket_number).first()

        if ticket:
            ticket.description = description
            ticket.assignee = assignee
            ticket.status = status

            if new_comment_text:
                comment = Comment(message=new_comment_text, username=username, created_on=created_on)
                ticket.comments.append(comment)

            if new_attachment_url:
                # Generate a unique object name for S3
                object_name = f"{ticket_number}/{new_attachment_url.split('/')[-1]}"
                # Upload file to S3 bucket
                upload_success = upload_file_to_s3(new_attachment_url, 'assignment3-ticketflow-attachments', object_name)
                if upload_success:
                    # If upload is successful, add the attachment URL to the ticket
                    attachment_url = f"https://assignment3-ticketflow-attachments.s3.amazonaws.com/{object_name}"
                    attachment = Attachment(url=attachment_url, username=username, created_on=created_on)
                    ticket.attachments.append(attachment)
                else:
                    return "Failed to upload attachment to S3. Please try again later."
            
            try:
                db.session.commit()
                return redirect(url_for('main'))
            except Exception as e:
                message = "Error updating ticket:", e
                db.session.rollback()
                return redirect(url_for('main'))
        else:
            return "Ticket not found."

@application.route('/ticket/<ticket_id>', methods=['GET'])
def view_ticket(ticket_id):
    if 'email' in session:
        user_id = session['email']
        user = User.query.filter_by(email=user_id).first()
        user_name = user.username if user else "Unknown"

        users = User.query.with_entities(User.username).all()
        users = [row[0] for row in users]

        ticket = Ticket.query.get(ticket_id)

        if ticket:
            return render_template('ticket.html', ticket=ticket, user_name=user_name, users=users)
        else:
            return "Ticket not found."
    return redirect(url_for('login'))

@application.route('/search', methods=['GET'])
def search_tickets():
    if request.method == 'GET':
        user_id = session.get('email')
        if not user_id:
            return redirect(url_for('login'))

        user = User.query.filter_by(email=user_id).first()
        user_name = user.username if user else "Unknown"

        users = User.query.with_entities(User.username).all()
        users = [row[0] for row in users]
        search_query = request.args.get('search_query')
        all_tickets = Ticket.query.all()
        query_tickets = Ticket.query.filter_by(ticket_number=search_query).all()
        ticket_data = [{'id': ticket.id, 'ticket_number': ticket.ticket_number, 'description': ticket.description[:200] + '...' if len(ticket.description) > 200 else ticket.description,  
                        'assignee': ticket.assignee, 'status': ticket.status, 'raised_by': ticket.raised_by, 'created_on': str(ticket.created_on)} 
                        for ticket in all_tickets]
        query_data = [{'id': ticket.id, 'ticket_number': ticket.ticket_number, 'description': ticket.description[:200] + '...' if len(ticket.description) > 200 else ticket.description,  'assignee': ticket.assignee, 'raised_by': ticket.raised_by, 'created_on': ticket.created_on.strftime("%Y-%m-%d %H:%M:%S")} for ticket in query_tickets]

        return render_template('search_results.html', query_data=query_data, user_name=user_name, users=users, tickets=ticket_data)

def print_tickets_table_schema():
    # Reflect the existing database tables
    db.reflect()

    # Get the metadata for the Ticket table
    ticket_table = db.Model.metadata.tables['tickets']

    # Print the column names and their types
    print("Tickets Table Schema:")
    for column in ticket_table.c:
        print(f"Column: {column.name}, Type: {column.type}")


@application.route('/apiticket', methods=['POST'])
def create_api_ticket():
    if request.method == 'POST':
        data = request.json 
        raised_by = data['raised_by'] if 'raised_by' in data else 'Unknown'
        description_html = data['description'] if 'description' in data else 'No Description'
        if description_html:
            description = BeautifulSoup(description_html, 'html.parser').get_text()
        else:
            description = ''
        
        # Find the last ticket raised by the customer
        existing_ticket = Ticket.query.filter_by(raised_by=raised_by).order_by(Ticket.created_on.desc()).first()

        if existing_ticket:
            # Add a comment to the existing ticket
            new_comment = Comment(
                message=description,
                created_on=str(datetime.now()),
                username=raised_by,
                ticket_id=existing_ticket.id
            )
            db.session.add(new_comment)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Comment added to existing ticket'})
        
        # If the customer doesn't have any existing tickets, create a new ticket
        ticket_number = generate_ticket_number()
        status = "new"
        created_on = str(datetime.now()) 
        new_ticket = Ticket(
            ticket_number=ticket_number,
            description=description,
            status=status,
            raised_by=raised_by,
            created_on=created_on,
            assignee='Unassigned'
        )
        db.session.add(new_ticket)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Ticket created successfully'})
    
def generate_ticket_number(prefix='T'):
    # Get the current timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[-6:]
    
    # Concatenate the prefix with the timestamp to create the ticket number
    ticket_number = f'{prefix}-{timestamp}'
    
    return ticket_number

# Function to upload file to S3 bucket
def upload_file_to_s3(file_path, bucket_name, object_name):
    s3 = boto3.client('s3')
    try:
        response = s3.upload_file(file_path, bucket_name, object_name)
        print("File uploaded successfully to S3.")
        return True
    except ClientError as e:
        print(f"Error uploading file to S3: {e}")
        return False

@application.route('/delete_ticket/<int:ticket_id>', methods=['POST'])
def delete_ticket(ticket_id):
    try:
        # Query the database for the ticket to delete
        ticket = Ticket.query.get(ticket_id)

        if ticket:
            # Delete all comments associated with the ticket
            Comment.query.filter_by(ticket_id=ticket_id).delete()

            # Delete all attachments associated with the ticket
            Attachment.query.filter_by(ticket_id=ticket_id).delete()

            # Delete the ticket from the database
            db.session.delete(ticket)
            db.session.commit()
            return redirect(url_for('main'))
        else:
            return jsonify({'error': f'Ticket with ID {ticket_id} not found'}), 404
    except Exception as e:
        # Handle database errors
        error_message = f"Error deleting ticket {ticket_id}: {e}"
        db.session.rollback()
        return jsonify({'error': error_message}), 500

    
if __name__ == "__main__":
    application.debug = True
    #app.run(host="127.0.0.1", port=8080, debug=True)
    application.run()
