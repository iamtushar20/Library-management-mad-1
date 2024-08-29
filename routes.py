from flask import render_template, request, redirect, url_for, flash, session, Response, make_response

from functools import wraps
from sqlalchemy import or_
from datetime import datetime
from sqlalchemy import func


from app import app

from models import db, User, Section, Book, BookIssue, BookRequest



def check_return_and_revoke(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        
        issues = BookIssue.query.filter_by(approved='Accepted').all()

        
        for issue in issues:
            # Checking if current date is greater than return date
            if datetime.now().date() > issue.return_date:
                # Updating approved status to 'Revoked'
                issue.approved = 'Revoked'
                # Updating return date to current date
                issue.return_date = datetime.now().date()
                # Commiting changes to the database
                db.session.commit()

        return func(*args, **kwargs)

    return wrapper




    
@app.route('/') # home route
def home():
    
    return render_template('home.html')

@app.route('/login') # login route for both user and admin
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST']) # route for filling username and password for login
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash('Username does not exist')
        return redirect(url_for('login'))
    
    if not user.password == password:
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    session['user_id'] = user.id

    if user.is_admin: # checking if user.is_admin is true and if it is then redirecting to admin url
        flash('Logged in Successfully @Admin', 'success')
        return redirect(url_for('admin'))
    
    else:
        flash('Logged in Successfully', 'success')
        return redirect(url_for('index'))


@app.route('/register')   # route for registering user
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    name = request.form.get('name')

    if not username or not password or not confirm_password:
        flash('Please fill out all fields')
        return redirect(url_for('register'))
    
    if '@' not in username:
        flash('Username must contain @ symbol')
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('register'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('register'))
    
    password_hash = password
    
    new_user = User(username=username, password=password_hash, name=name)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))



# Authenticating Decorators for User login and Admin login
        
def login_required(func):
    @wraps(func)
    def check(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('login'))
    return check


def admin_required(func):
    @wraps(func)
    def check(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You are not authorized to access this page')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return check



@app.route('/profile')  # route for profile of user or admin
@login_required
@check_return_and_revoke
def profile():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return render_template('admin_profile.html', user=user)
    return render_template('profile.html', user=user)


@app.route('/profile', methods=['POST'])  # route for user and admin to change password and update name
@login_required
@check_return_and_revoke
def profile_post():
    # username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')

    if not cpassword:
        flash('Current password is required')
        return redirect(url_for('profile'))
    
    user = User.query.get(session['user_id'])
    if not user.password == cpassword:
        flash('Incorrect password')
        return redirect(url_for('profile'))
    
    if not password:
        user.name = name
    else:
        if not password:
            flash('New password is required')
            return redirect(url_for('profile'))

        
        user.password = password
        user.name = name
    
  
    
    
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))

@app.route('/logout') # logout route
@login_required
@check_return_and_revoke
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))


# Admin pages are from here on

@app.route('/admin') # this is route for admin home page
@login_required
@admin_required
@check_return_and_revoke
def admin():
    sections = Section.query.all()
    books = Book.query.all()
    book_issues = BookIssue.query.all()
    book_requests = BookRequest.query.all()
    
    return render_template('admin.html', sections=sections, books=books, book_issues=book_issues, book_requests=book_requests)


@app.route('/section/add') # route for rendering a form to add section
@check_return_and_revoke
@admin_required
def add_section():
    return render_template('section/add.html')

@app.route('/section/add', methods=['POST']) # route for adding form data to database
@check_return_and_revoke
@admin_required
def add_section_post():
    name = request.form.get('name')
    date_str = request.form.get('date_created')
    date_created = datetime.strptime(date_str, '%Y-%m-%d').date()
    description = request.form.get('description')

    if not name or not date_created or not description:
        flash('Please fill out all fields')
        return redirect(url_for('add_section'))
    
    current_datetime = datetime.now()

    current_date = current_datetime.date()

    # Comparing the date_created with the current_date
    if date_created < current_date:
        flash('Please Enter a valid date i.e from today\'s date' )
        return redirect(url_for('add_section'))
    
    section_in_db = Section.query.filter_by(name=name).first()

    if section_in_db:
        # Section with the specified name exists, redirect to section route
        flash('Section with the specified name exists')
        return redirect(url_for('add_section'))
  
    
    section = Section(name=name, date_created=current_date, description=description)
    db.session.add(section)
    db.session.commit()

    flash('Section added successfully')
    return redirect(url_for('admin_section_show'))



@app.route('/section/<int:id>/') # route for seeing a particular section and their books
@check_return_and_revoke
@admin_required
def show_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/show.html', section=section)

@app.route('/section/<int:id>/edit')  # route for  rendering a form to edit a section
@admin_required
@check_return_and_revoke
def edit_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exists')
        return redirect(url_for('admin'))
    
    
    return render_template('section/edit.html', section = section)

@app.route('/section/<int:id>/edit', methods=['POST'])  # route for adding edit section's  form data to database
@admin_required
@check_return_and_revoke
def edit_section_post(id):
    section = Section.query.get(id)
    
    if not section:
        flash('Section does not exists')
        return redirect(url_for('admin'))
    name = request.form.get('name')
    date_str = request.form.get('date_created')
    date_created = datetime.strptime(date_str, '%Y-%m-%d').date()
    description = request.form.get('description')

    if not name or not date_created or not description:
        flash('Please fill out all fields')
        return redirect(url_for('edit_section',id=id))
    if name != section.name:
        # Check if a section with the new name already exists in the database
        existing_section = Section.query.filter(Section.name == name).first()
        if existing_section:
            flash('A section with the same name already exists. Cannot update.')
            return redirect(url_for('edit_section', id=id))



    section.name =name
    section.date_created = date_created
    section.description = description
    db.session.commit()

    flash('Section edited Successfully')
    return redirect(url_for('admin_section_show'))


@app.route('/section/<int:id>/delete') # route for rendering a  form for deleting a section
@admin_required
@check_return_and_revoke
def delete_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/delete.html', section=section)

@app.route('/section/<int:id>/delete', methods=['POST']) # route for pushing the changes in database after the deletion of a particular section
@admin_required
@check_return_and_revoke
def delete_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    books = Book.query.filter_by(section_id=id).all()
    
    for book in books:
        # Delete related book issues
        related_book_issues = BookIssue.query.filter_by(book_name=book.name).all()
        for issue in related_book_issues:
            db.session.delete(issue)
        
        related_book_requests = BookRequest.query.filter_by(book_name=book.name).all()
        for req in related_book_requests:
            db.session.delete(req)
            db.session.commit()
        
        # Delete the book itself
        db.session.delete(book)


       
        
    db.session.delete(section)
    db.session.commit()

    flash('Section deleted successfully')
    return redirect(url_for('admin_section_show'))


# Starting from here, the routes for managing books are defined

@app.route('/book/add/<int:section_id>') # Renders a form to add a new book to a specific section.
@admin_required
@check_return_and_revoke
def add_book(section_id):

    sections = Section.query.all()
    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exists')
        return redirect(url_for('admin'))
    return render_template('book/add.html', section=section, sections=sections)
    

@app.route('/book/add/', methods=['POST']) # Handles the form submission to add a new book to a section.
@admin_required
@check_return_and_revoke
def add_book_post():

    section_id = request.form.get('section_id')
    name = request.form.get('name')
    content = request.form.get('content')
    authors = request.form.get('authors')
    date_iss = request.form.get('date_added')
    date_added = datetime.strptime(date_iss, '%Y-%m-%d').date()
    price = request.form.get('price')
   

    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    
    if not name or not content or not authors or not date_added or not price :
        flash('Please fill out all fields')
        return redirect(url_for('add_book', section_id=section_id))
    

    current_datetime = datetime.now()

    current_date = current_datetime.date()

    # Comparing the date_created with the current_date
    if date_added < current_date:
        flash('Please Enter a valid date i.e from today\'s date' )
        return redirect(url_for('add_book', section_id=section_id))
    
    book_in_db = Book.query.filter_by(name=name).first()

    if book_in_db:
        # Book with the specified name exists, redirect to book route
        flash('Book with specified name exists')
        return redirect(url_for('add_book', section_id=section_id))
    
    
    book = Book(
            section_id=section_id,
            name=name,
            content=content,
            authors=authors,
            date_added=current_date,
            price=price
            
        )
    
    db.session.add(book)
    db.session.commit()

    flash('Book added Successfully')
    return redirect(url_for('show_section', id=section_id))

@app.route('/book/<int:id>/edit') # Description: Route for displaying the edit form for a specific book by its ID
@admin_required
@check_return_and_revoke
def edit_book(id):
    sections = Section.query.all()
    book = Book.query.get(id)
    return render_template('book/edit.html', sections=sections, book=book)



@app.route('/book/<int:id>/edit', methods=['POST']) # route for updating the books with form data 
@admin_required
@check_return_and_revoke
def edit_book_post(id):
    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    
    section_id = request.form.get('section_id')
    name = request.form.get('name')
    content = request.form.get('content')
    authors = request.form.get('authors')
    date_iss = request.form.get('date_added')
    date_added = datetime.strptime(date_iss, '%Y-%m-%d').date()
    price = request.form.get('price')

    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    
    if not name or not content or not authors or not date_added or not price:
        flash('Please fill out all fields')
        return redirect(url_for('edit_book', id=id))
    
    # book_in_db = Book.query.filter_by(name=name).count()
    if name != book.name:
        # Check if a book with the new name already exists in the database
        existing_book = Book.query.filter(Book.name == name).first()
        if existing_book:
            flash('A book with the same name already exists. Cannot update.')
            return redirect(url_for('edit_book', id=id))

    
    
    # Update the attributes of the Book object
    book.name = name
    book.content = content
    book.authors = authors
    book.date_added = date_added
    book.price = price
    
    # Commit the changes to the database
    db.session.commit()

    flash('Book updated successfully')
    return redirect(url_for('show_section', id=section_id))

@app.route('/book/<int:id>/delete')  #Description: # Route for rendering the delete book confirmation page
@admin_required
@check_return_and_revoke
def delete_book(id):
    book= Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    return render_template('book/delete.html', book=book)


@app.route('/book/<int:id>/delete', methods=['POST'])  #Description: Route for deleting a book
@admin_required
@check_return_and_revoke
def delete_book_post(id):
    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    
    
    related_book_issues = BookIssue.query.filter_by(book_name=book.name).all()
    for issue in related_book_issues:
        db.session.delete(issue)
        
    related_book_requests = BookRequest.query.filter_by(book_name=book.name).all()
    for req in related_book_requests:
        db.session.delete(req)
        
       
            
        
    section_id = book.section.id
    db.session.delete(book)
    db.session.commit()

    flash('Book deleted Successfully')
    return redirect(url_for('show_section', id=section_id))


@app.route('/book/all_book') # Route for seeing all the books 
@admin_required
@check_return_and_revoke
def all_books():
    all_books = Book.query.all()
    params = request.args.get('params')
    query = request.args.get('query')
    sections = Section.query.all()

    if params == 'section_name':
        sections = Section.query.filter(Section.name.ilike(f'%{query}%')).all()
        return render_template('all_books.html', sections=sections)
    elif params == 'book_name':
        sections = Section.query.join(Section.books).filter(Book.name.ilike(f'%{query}%')).all()
        return render_template('all_books.html', sections=sections, param = params, book_name = query)
    elif params == 'author_name':
        sections = Section.query.join(Section.books).filter(Book.authors.ilike(f'%{query}%')).all()
        return render_template('all_books.html',sections = sections, param = params , author_name = query)
    
    
    return render_template('all_books.html', sections=sections) 

 



@app.route('/admin/book_requests') # route for admin to see all the book requests made by user
@admin_required
@check_return_and_revoke
def admin_book_requests():
    book_requests = BookRequest.query.all()

    if not book_requests:
        flash('No new request found')
        return redirect(url_for('admin'))
    return render_template('admin_book_requests.html', book_requests=book_requests)

@app.route('/admin/book_issued_list') # route for admin to see issued book list
@check_return_and_revoke
@admin_required
def admin_book_issued_list():
    book_issues = BookIssue.query.all()
    if not book_issues:
        flash('Currently No book is issued')
        return redirect(url_for('admin'))
    return render_template('book_issued_list.html', book_issues=book_issues)



@app.route('/admin/show/section') # route for admin to see all the sections
@check_return_and_revoke
@admin_required
def admin_section_show():
    sections = Section.query.all()
    return render_template('show_section.html', sections=sections)



@app.route('/book/request/accept/<status>/<int:id>') # route for accepting book request 
@check_return_and_revoke
@admin_required
def book_accept(status, id):
    book_req = BookRequest.query.get(id)
    books = Book.query.filter_by(name= book_req.book_name).first()
    name = book_req.user_name
    book_issue = BookIssue.query.filter(BookIssue.user_name == name, BookIssue.approved =='Accepted')
    book_issues_count = book_issue.count()

    if book_issues_count  == 5:
        user_name=book_req.user_name
        book_name= books.name
        book_author=books.authors
        issue_date=book_req.request_date
        return_date=book_req.return_date
    
        approved='Declined'
    
    

        book_issue = BookIssue(
            user_name=user_name,
            book_name=book_name,
            book_author=book_author,
            issue_date=issue_date,
            return_date=return_date,
            approved=approved,

        
        )
    

        # Add the BookIssue to the session and commit changes
        db.session.add(book_issue)
        db.session.commit()

        db.session.delete(book_req)
        db.session.commit()

        flash('user have already issued 5 books')
        return redirect(url_for('admin_book_requests'))
    
    if book_req:
        # Update the status to "accepted"
        # book_req.status = "Accepted"
        db.session.commit()
    else:
        flash('Book Request not found')
        return redirect(url_for('admin'))
    
    current_datetime = datetime.now()

    current_date = current_datetime.date()
    
    user_name=book_req.user_name
    book_name= books.name
    book_author=books.authors
    issue_date=current_date
    return_date=book_req.return_date
    
    approved='Accepted'
    read=books.content
    

    book_issue = BookIssue(
        user_name=user_name,
        book_name=book_name,
        book_author=book_author,
        issue_date=issue_date,
        return_date=return_date,
        approved=approved,
        read=read
    )
    
    db.session.add(book_issue)
    db.session.commit()

    db.session.delete(book_req)
    db.session.commit()

    flash('Book Request Accepted Successfully')

    return redirect(url_for('admin_book_requests'))
    

@app.route('/book/request/reject/<status>/<int:id>') # route for rejecting the book request 
@check_return_and_revoke
@admin_required
def book_reject(status, id):
    book_req = BookRequest.query.get(id)
    books = Book.query.filter_by(name= book_req.book_name).first()
    if book_req:

        book_req.status == "Rejected"
        db.session.commit()
    else:
        
        flash('Book  Request not found')
        return redirect(url_for('admin'))
    
    user_name=book_req.user_name
    book_name= books.name
    book_author=books.authors
    issue_date=book_req.request_date
    return_date=book_req.return_date
    
    approved='Declined'
    
    

    book_issue = BookIssue(
        user_name=user_name,
        book_name=book_name,
        book_author=book_author,
        issue_date=issue_date,
        return_date=return_date,
        approved=approved,

        
    )
    

     # Add the BookIssue to the session and commit changes
    db.session.add(book_issue)
    db.session.commit()

    db.session.delete(book_req)
    db.session.commit()
    flash('Book request Declined')

    return redirect(url_for('admin_book_requests'))


@app.route('/book/revoke/<int:id>') # admin's route to revoke a book
@check_return_and_revoke
@admin_required
def book_revoke(id):
    issue = BookIssue.query.get(id)

    if not issue:
        flash('Book not found')
        return redirect(url_for('admin'))

     # Check if the status is "Accepted"
    if issue.approved == 'Accepted':
        # Update the status to "Declined"
        issue.approved = 'Revoked'
        # Commit the changes to the database
        issue.return_date = datetime.now().date()
        db.session.commit()
        flash('Book Revoked successfully')
    else:
        flash ('Status is not "Accepted", cannot change')
    
    return redirect(url_for('admin'))




def unique_accepted_books():
    
    unique_books = (
        BookIssue.query
        .with_entities(BookIssue.book_name)
        .filter_by(approved='Accepted')
        .distinct()
        .all()
    )
    
    return unique_books
 
@app.route('/book/status') # admin's route to see issued books list and see their status and feedback
@admin_required
@check_return_and_revoke
def book_status():
    book_issue= BookIssue.query.all()
    unique_book_names = unique_accepted_books()

    if not book_issue:
        flash('Book not found')
        return redirect(url_for('admin'))
    
    return render_template('book_status.html', book_issue=book_issue, unique_book_names=unique_book_names)

def get_user(book_name):
    book_issues = BookIssue.query.filter_by(book_name=book_name, approved='Accepted').all()
    users_issued = [(issue.user_name, issue.issue_date, issue.return_date) for issue in book_issues]
    return users_issued



@app.route('/book/status/info/<name>') # admin's route to see book's status to whom it have been issued
@check_return_and_revoke
@admin_required
def book_status_info(name):
    users_issued = get_user(name)
    book_issues = BookIssue.query.filter_by(book_name=name).all()

    if not book_issues:
        flash ('Book not found')
        return redirect(url_for('admin'))
    
    return render_template('book_status_info.html', name=name, users_issued=users_issued)




def user_with_feedback(book_name): 
    
    book_issues_with_feedback = BookIssue.query.filter_by(book_name=book_name).filter(BookIssue.feedback.isnot(None)).all()
    users_with_feedback = [(issue.user_name, issue.feedback) for issue in book_issues_with_feedback]
    return users_with_feedback

@app.route('/feedback/read/<name>') # route to see the feedback for a book if given by the user
@check_return_and_revoke
@admin_required
def see_feedback(name):
    user_feedback = user_with_feedback(name)
    return render_template('see_feedback.html', user_feedback= user_feedback, name = name)



@app.route('/dashboard') # route for admin's dashboard
@check_return_and_revoke
@admin_required
def dashboard():
    sections = Section.query.all()
    section_count = len(sections)
    books = Book.query.all()
    book_count = len(books)
    users = User.query.all()
    user_count = len(users)
    book_issues = BookIssue.query.filter_by(approved='Accepted').all()
    book_issue_count = len(book_issues)
    book_request = BookRequest.query.filter_by(status='pending').all()
    book_request_count = len(book_request)
    
    sections_data = db.session.query(Section.name, func.count(Book.id)).join(Book).group_by(Section.name).all()
    formatted_data = [{'section_name': row[0], 'book_count': row[1]} for row in sections_data]

    # Query to get the count of each book issued
    issued_books = db.session.query(BookIssue.book_name, func.count(BookIssue.id)).filter(
        (BookIssue.approved == 'Accepted') | (BookIssue.approved == 'Returned') | (BookIssue.approved == 'Revoked')
    ).group_by(BookIssue.book_name).all()

    # Sort the books based on their issuance count in descending order
    sorted_books = sorted(issued_books, key=lambda x: x[1], reverse=True)

    # Get the top 5 most frequently issued books
    top_books = sorted_books[:5]

    # Prepare data for the chart
    labels = [book[0] for book in top_books]  # Book names
    counts = [book[1] for book in top_books]  # Issuance counts

    return render_template('dashboard.html', user_count=user_count, book_count=book_count,
                           section_count=section_count, book_issue_count=book_issue_count, book_request_count=book_request_count ,section_data = formatted_data, top_books_labels=labels, top_books_counts=counts)


   



# ------------------------------------------------------------------------------------------------------------------------------------------

#From here onwards user routes are defined

@app.route('/index') # route for user home page
@login_required
@check_return_and_revoke
def index():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin')) # this will redirect to admin home page on the basis of is_admin = True
    

    params = request.args.get('params')
    query = request.args.get('query')
    sections = Section.query.all()

    if params == 'section_name':
        sections = Section.query.filter(Section.name.ilike(f'%{query}%')).all()
        return render_template('index.html', sections=sections)
    elif params == 'book_name':
        sections = Section.query.join(Section.books).filter(Book.name.ilike(f'%{query}%')).all()
        return render_template('index.html', sections=sections, param = params, book_name = query)
    elif params == 'author_name':
        sections = Section.query.join(Section.books).filter(Book.authors.ilike(f'%{query}%')).all()
        return render_template('index.html',sections = sections, param = params , author_name = query)
    return render_template('index.html', sections=sections)




@app.route('/book/request/<int:book_id>') # route for user to get a request form to  request a book by clicking on Request button
@check_return_and_revoke
@login_required
def book_request(book_id):
    book=Book.query.get(book_id)
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found')
        return redirect(url_for('index'))
    if not book:
        flash('Book not found')
        return redirect(url_for('index'))
    book_issue = BookIssue.query.filter(BookIssue.user_name == user.username, BookIssue.approved =='Accepted')
    book_issues_count = book_issue.count()

    if book_issues_count  == 5:
        flash('You cannot issue more than 5 books')
        return redirect(url_for('index'))
    
    book_request = BookRequest.query.filter(BookRequest.user_name == user.username, BookRequest.status =='pending')
    book_request_count = book_request.count()

    if book_request_count == 5:
        flash('You cannot request more than 5 book')
        return redirect(url_for('index'))
    
    total_count = book_issues_count + book_request_count

    if total_count == 5:
        flash(f'You already have {book_request_count} request pending and  have issued {book_issues_count} books')
        return redirect(url_for('index'))

    return render_template('book_request.html', book=book, user=user)


@app.route('/book/request/<int:book_id>', methods=['POST']) # route for user to fill the details in form and submit
@check_return_and_revoke
@login_required
def book_request_post(book_id):
    user_name = request.form.get('user_name')
    book_name = request.form.get('book_name')
    date_str = request.form.get('request_date')
    request_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    date_ret = request.form.get('return_date')
    return_date = datetime.strptime(date_ret, '%Y-%m-%d').date()
    # Convert to integer

    # Check if user exists
    user = User.query.filter_by(username=user_name).first()
    if user is None:
        flash('User not found')
        return redirect(url_for('index'))
    if not user_name or not book_name or not request_date or not return_date:
        flash('Please fill all input fields')
        return redirect(url_for('index'))

    book_id = Book.query.get(book_id)

    current_datetime = datetime.now()

    current_date = current_datetime.date()
    
    if request_date < current_date:
        flash('Please enter a valid request date')
        return redirect(url_for('index'))


    
    if request_date > return_date:
        flash('Return date cannot be before request date')
        return redirect(url_for('index'))
    request_check = BookRequest.query.filter_by(user_name=user_name).all()
    if request_check:
        for req in request_check:
            if req.book_name == book_name:
                flash('You have already requested for this book')
                return redirect(url_for('index'))
    
    # Check if book exists
    book = Book.query.filter_by(name=book_name).first()
    if book is None:
        flash('Book not found')
        return redirect(url_for('index'))
    
    book_issued_already = BookIssue.query.filter(BookIssue.user_name == user.username, 
                                                 BookIssue.book_name == book_name, 
                                                 BookIssue.approved =='Accepted').first()
    if book_issued_already:
        flash('You have already issued this book')
        return redirect(url_for('index'))

    # Create and add a new BookRequest object
    request_book = BookRequest(
        user_name=user_name,
        book_name=book_name,
        request_date=request_date,
        return_date=return_date,
        
    )
    db.session.add(request_book)
    db.session.commit()

    flash('Book requested successfully')
    return redirect(url_for('index'))



@app.route('/user/book_issue/history') # user's route to see the book issue history
@login_required
@check_return_and_revoke

def user_book_issue_history():
    user = User.query.get(session['user_id'])
    username=user.username

  
    book_issue = BookIssue.query.filter_by(user_name=username)
    
    if not book_issue:
        flash('Issue history not found')
        return redirect(url_for('index'))
    
    return render_template('user_request_history.html',book_issue=book_issue )


@app.route('/user/book_issue') # user's route to see issued book
@login_required
@check_return_and_revoke

def user_book_issue():
    user = User.query.get(session['user_id'])
    username=user.username

    book_issue = BookIssue.query.filter_by(user_name=username)

    if not book_issue:
        flash('Book not found')
        return redirect(url_for('index'))

    return render_template('user_book_issue.html',book_issue=book_issue )


@app.route('/user/book_return/<int:id>') # user's route to return a book
@login_required
@check_return_and_revoke
def user_book_return(id):
    issue = BookIssue.query.get(id)

    if not issue:
        flash('Book not found')
        return redirect(url_for('index'))
    issue.return_date = datetime.now().date()
    issue.approved = 'Returned'
    db.session.commit()
    flash('Book returned successfully ! ')

    return redirect(url_for('index'))



@app.route('/book/content/<name>') # route for read book content
@check_return_and_revoke
@login_required
def get_book_content(name):
    book = Book.query.filter_by(name=name).first()
    
    if not book:
        flash('Book not found')
        return redirect(url_for('user_book_issue'))
    
    return render_template('book_content.html', book=book)


@app.route('/feedback/<int:id>') # route for rendering feedback form for a book
@check_return_and_revoke
@login_required
def feedback(id):

    issue_book = BookIssue.query.get(id)

    if not issue_book:
        flash('Book not found')
        return redirect(url_for('user_book_issue'))
    
    return render_template('feedback.html', id = id)


@app.route('/feedback/<int:id>', methods = ['POST']) # route for pushing feedback to the database
@check_return_and_revoke
@login_required
def feedback_post(id):
    feedback = request.form.get('feedback')

    issue_book = BookIssue.query.get(id)
    if not issue_book:
        flash('Book not found')
        return redirect(url_for('user_book_issue'))
    issue_book.feedback = feedback

    db.session.commit()
    return redirect(url_for('user_book_issue'))



@app.route('/book/payment/<int:book_id>') # route for payment page for a book
@check_return_and_revoke
@login_required
def book_payment(book_id):
    book = Book.query.get(book_id)
    content = book.content
    filename = book.name
    user_id = session['user_id']
    user = User.query.get(user_id)

    if not book:
        flash('Book not Found')
        return redirect(url_for('index'))
    return render_template('payment.html', book=book, user=user )

@app.route('/book/download/<name>') # route for downloading book for a price
@check_return_and_revoke
@login_required
def download_book(name):
    book = Book.query.filter_by(name=name).first()
    
    if not book:
        flash('Book not found')
        return redirect(url_for('index'))
    
    return render_template('download.html', book=book)



