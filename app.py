# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, flash, redirect, url_for, abort
from flask.ext.sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, validators, ValidationError
from itsdangerous import URLSafeSerializer

app = Flask(__name__, instance_relative_config=True)
db = SQLAlchemy(app)

# Load the default configuration
app.config.from_object('config')

# Load the configuration from the instance folder
app.config.from_pyfile('config.py')

s = URLSafeSerializer(app.config['SECRET_KEY'])


class Request(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    email = db.Column(db.String(120))
    generation_date = db.Column(db.Date())

    def __init__(self, id, email, generation_date=None):
        self.id = id
        self.email = email
        self.generation_date = generation_date

    def __repr__(self):
        return "<Request {} - {} - {}>".format(
                self.id,
                self.email,
                self.generation_date
                )


def id_does_not_exist(form, field):
    if db.session.query(Request.id).filter(Request.id == field.data).count():
        raise ValidationError('Id already exists.')


class RequestForm(Form):
    id = StringField(
            'ID',
            [
                validators.Length(min=4, max=32),
                validators.Required(),
                validators.Regexp(
                    "^[a-z]+[a-z\-]*$",
                    message="Must be lowercase and can contain '-'."
                    ),
                id_does_not_exist
            ]
            )
    email = StringField(
            'E-Mail',
            [
                validators.Email(), validators.Required(),
                validators.EqualTo('email_confirm')
            ]
            )
    email_confirm = StringField('E-Mail')
    captcha = StringField(
            u'Rätsel',
            validators=[
                validators.AnyOf(
                    ['Berlin', 'berlin'],
                    message="Incorrect. If you keep having trouble contact the mailing list."  # noqa
                    ),
                validators.Required()
            ]
    )


@app.route('/', methods=['GET', 'POST'])
def index():
    form = RequestForm(request.form)
    if request.method == 'POST' and form.validate():
        req = Request(form.id.data, form.email.data)
        db.session.add(req)
        db.session.commit()
        token = s.dumps(req.id, salt='freifunk-ca-service')
        confirm_url = url_for('get_certificate',
                              token=token,
                              _external=True)

        return render_template('thanks.html')
    return render_template('index.html', form=form)


@app.route('/certificates/<token>', methods=['GET'])
def get_certificate(token):
    try:
        id = s.loads(token, salt='freifunk-ca-service')
    except:
        abort(404)

    ca_req = Request.query.get_or_404(id)
    print(ca_req)

    return "return key + cert here + {}".format(ca_req)
