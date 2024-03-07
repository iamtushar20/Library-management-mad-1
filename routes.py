from flask import Flask, render_template, request, redirect, url_for, flash, session

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime


from app import app

from models import db, User, Section, Book, BookIssue, BookRequest



# Routes are started from here
    
@app.route('/')
def home():
    
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
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
    
    if not check_password_hash(user.password, password):
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    session['user_id'] = user.id
    if user.is_admin:
        flash('Logged in as admin', 'success')
        # -----------------------------------------
        
        return redirect(url_for('admin'))
    # ------------------------------------------------------
    else:
        flash('Logged in as a normal user', 'success')
        return redirect(url_for('index'))


@app.route('/register')
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
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('register'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('register'))
    
    password_hash = generate_password_hash(password)
    
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

@app.route('/index')
def index():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    sections = Section.query.all()

    return render_template('index.html', sections=sections)









@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/profile', methods=['POST'])
@login_required
def profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')

    if not username or not cpassword or not password:
        flash('Please fill out all the required fields')
        return redirect(url_for('profile'))
    
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.password, cpassword):
        flash('Incorrect password')
        return redirect(url_for('profile'))
    
    if username != user.username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('profile'))
    
    new_password_hash = generate_password_hash(password)
    user.username = username
    user.password = new_password_hash
    user.name = name
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))


# Admin pages are from here on

@app.route('/admin')
# @admin_required
def admin():
    sections = Section.query.all()
    books = Book.query.all()
    book_issues = BookIssue.query.all()
    # section_names = []
    return render_template('admin.html', sections=sections, books=books, book_issues=book_issues)


@app.route('/section/add')
def add_section():
    return render_template('section/add.html')

@app.route('/section/add', methods=['POST'])
# @admin_required
def add_section_post():
    name = request.form.get('name')
    date_str = request.form.get('date_created')
    date_created = datetime.strptime(date_str, '%Y-%m-%d').date()
    description = request.form.get('description')

    if not name:
        flash('Please fill out all fields')
        return redirect(url_for('add_section'))
    
    section = Section(name=name, date_created=date_created, description=description)
    db.session.add(section)
    db.session.commit()

    flash('Section added successfully')
    return redirect(url_for('admin'))



@app.route('/section/<int:id>/')
# @admin_required
def show_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/show.html', section=section)

@app.route('/section/<int:id>/edit')
# @admin_required
def edit_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exists')
        return redirect(url_for('admin'))
    return render_template('section/edit.html', section = section)

@app.route('/section/<int:id>/edit', methods=['POST'])
# @admin_required
def edit_section_post(id):
    section = Section.query.get(id)
    
    if not section:
        flash('Section does not exists')
        return redirect(url_for('admin'))
    name = request.form.get('name')
    date_str = request.form.get('date_created')
    date_created = datetime.strptime(date_str, '%Y-%m-%d').date()
    description = request.form.get('description')

    if not name:
        flash('Please fill out all fields')
        return redirect(url_for('edit_section',id=id))
    
    section.name =name
    section.date_created = date_created
    section.description = description
    db.session.commit()

    flash('Section edited Successfully')
    return redirect(url_for('admin'))


@app.route('/section/<int:id>/delete')
@admin_required
def delete_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/delete.html', section=section)

@app.route('/section/<int:id>/delete', methods=['POST'])
@admin_required
def delete_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    db.session.delete(section)
    db.session.commit()

    flash('Section deleted successfully')
    return redirect(url_for('admin'))


@app.route('/book/add/<int:section_id>')
@admin_required
def add_book(section_id):
    sections = Section.query.all()
    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exists')
        return redirect(url_for('admin'))
    return render_template('book/add.html', section=section, sections=sections)
    

@app.route('/book/add/', methods=['POST'])
@admin_required
def add_book_post():

    section_id = request.form.get('section_id')
    name = request.form.get('name')
    content = request.form.get('content')
    authors = request.form.get('authors')
    date_iss = request.form.get('date_added')
    date_added = datetime.strptime(date_iss, '%Y-%m-%d').date()
   

    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    
    if not name or not content or not authors :
        flash('Please fill out all fields')
        return redirect(url_for('add_book', section_id=section_id))
    
    book = Book(
            section_id=section_id,
            name=name,
            content=content,
            authors=authors,
            date_added=date_added,
            
        )
    
    db.session.add(book)
    db.session.commit()

    flash('Book added Successfully')
    return redirect(url_for('show_section', id=section_id))

@app.route('/book/<int:id>/edit')
@admin_required
def edit_book(id):
    sections = Section.query.all()
    book = Book.query.get(id)
    return render_template('book/edit.html', sections=sections, book=book)



@app.route('/book/<int:id>/edit', methods=['POST'])
@admin_required
def edit_book_post(id):

    section_id = request.form.get('section_id')
    name = request.form.get('name')
    content = request.form.get('content')
    authors = request.form.get('authors')
    date_iss = request.form.get('date_issued')
    date_added = datetime.strptime(date_iss, '%Y-%m-%d').date()
   

    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    
    if not name or not content or not authors :
        flash('Please fill out all fields')
        return redirect(url_for('add_book', section_id=section_id))
    
    book = Book(
            section_id=section_id,
            name=name,
            content=content,
            authors=authors,
            date_issued=date_added
        )
    
    
    db.session.commit()

    flash('Book updated Successfully')
    return redirect(url_for('show_section', id=section_id))

@app.route('/book/<int:id>/delete')
@admin_required
def delete_book(id):
    book= Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    return render_template('book/delete.html', book=book)


@app.route('/book/<int:id>/delete', methods=['POST'])
@admin_required
def delete_book_post(id):
    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    section_id = book.section.id
    db.session.delete(book)
    db.session.commit()

    flash('Book deleted Successfully')
    return redirect(url_for('show_section', id=section_id))



    

@app.route('/book/request/<int:book_id>')
def book_request(book_id):
    book=Book.query.get(book_id)
    user_id = session['user_id']
    user = User.query.get(user_id)
    return render_template('book_request.html', book=book, user=user)


@app.route('/book/request/<int:book_id>', methods=['POST'])
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
        return "User not found", 404

    # Check if book exists
    book = Book.query.filter_by(name=book_name).first()
    if book is None:
        return "Book not found", 404

    # Create and add a new BookRequest object
    request_book = BookRequest(
        user_name=user_name,
        book_name=book_name,
        request_date=request_date,
        return_date=return_date,
        
    )
    db.session.add(request_book)
    db.session.commit()

    # Redirect to a success page or any other route
    # return redirect(url_for('success_route'))
    flash('Book requested successfully')

    return redirect(url_for('index'))


        



@app.route('/admin/book_requests')
@admin_required
def admin_book_requests():
    book_requests = BookRequest.query.all()
    return render_template('admin_book_requests.html', book_requests=book_requests)



    


@app.route('/book/request/accept/<status>/<int:id>')
@admin_required
def book_accept(status, id):
    book_req = BookRequest.query.get(id)
    books = Book.query.filter_by(name= book_req.book_name).first()
    if book_req:
        # Update the status to "accepted"
        book_req.status == "Accepted"
        db.session.commit()
    else:
        # Handle the case where the BookRequest with the provided ID does not exist
        return "Book request not found", 404
    user_name=book_req.user_name
    book_name= books.name
    book_author=books.authors
    issue_date=book_req.request_date
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
    

     # Add the BookIssue to the session and commit changes
    db.session.add(book_issue)
    db.session.commit()

    db.session.delete(book_req)
    db.session.commit()

    return redirect(url_for('admin_book_requests'))
    

@app.route('/book/request/reject/<status>/<int:id>')
@admin_required
def book_reject(status, id):
    book_req = BookRequest.query.get(id)
    books = Book.query.filter_by(name= book_req.book_name).first()
    if book_req:
        # Update the status to "accepted"
        book_req.status == "rejected"
        db.session.commit()
    else:
        # Handle the case where the BookRequest with the provided ID does not exist
        return "Book request not found", 404
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

    return redirect(url_for('admin_book_requests'))
   


@app.route('/user/book_issue/history')
@login_required
def user_book_issue_history():
    user = User.query.get(session['user_id'])
    username=user.username

  
    book_issue = BookIssue.query.filter_by(user_name=username)
    
    
    
    return render_template('user_request_history.html',book_issue=book_issue )


@app.route('/user/book_issue')
@login_required
def user_book_issue():
    user = User.query.get(session['user_id'])
    username=user.username

  
    book_issue = BookIssue.query.filter_by(user_name=username)
    
    
    
    return render_template('user_book_issue.html',book_issue=book_issue )


@app.route('/user/book_return/<int:id>')
@login_required
def user_book_return(id):
    issue = BookIssue.query.get(id)

    # Update the return date to the current date
    issue.return_date = datetime.now().date()

    # Update any other relevant information, such as changing the status
    # For example, if you want to mark the status as "Returned"
    issue.approved = 'Returned'

    # Commit the changes to the database
    db.session.commit()
    flash('Book returned successfully ! ')

    return redirect(url_for('index'))

@app.route('/book/status')
@admin_required
def book_status():
    book_issue= BookIssue.query.all()
    return render_template('book_status.html', book_issue=book_issue)


@app.route('/book/status/info/<name>')
@admin_required
def book_status_info(name):
    book_issues = BookIssue.query.filter_by(book_name=name).all()
    
    return render_template('book_status_info.html', book_issues=book_issues)


@app.route('/book/revoke/<int:id>')
def book_revoke(id):
    issue = BookIssue.query.get(id)

     # Check if the status is "Accepted"
    if issue.approved == 'Accepted':
        # Update the status to "Declined"
        issue.approved = 'Revoked'
        # Commit the changes to the database
        db.session.commit()
        flash('Status updated successfully')
    else:
        flash ('Status is not "Accepted", cannot change')
    
    return redirect(url_for('admin'))

@app.route('/refresh')
def check_and_update_status():
    # Get all BookIssue records
    issues = BookIssue.query.filter_by(approved='Approved').all()

    # Iterate over each issue
    for issue in issues:
        # Check if current date is greater than return date
        if datetime.now().date() > issue.return_date:
            # Update approved status to 'Revoked'
            issue.approved = 'Revoked'
            # Update return date to current date
            issue.return_date = datetime.now().date()
            # Commit changes to the database
            db.session.commit()
    return redirect(url_for('admin'))


@app.route('/test')
def test():
    return render_template('testing_form_style.html')