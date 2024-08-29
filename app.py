from flask import Flask, render_template, request, redirect, url_for, flash, session


app = Flask(__name__)

app.secret_key='12341234'

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydatalbm.sqlite3"


from routes import *


if __name__ == '__main__':
    app.run(debug=True,)