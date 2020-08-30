from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SelectField, IntegerField, FloatField, RadioField, DateField, SubmitField, PasswordField, FieldList, FormField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from opghelper import  mongo

class LoginForm(FlaskForm):
    username = StringField('Korisničko ime', validators=[DataRequired()])
    password = PasswordField('Lozinka')
    submit = SubmitField('Prijavi se')   

class AdressForm(FlaskForm):
    zupanija = SelectField('Županija', validators=[DataRequired()], choices=[])
    opcina = SelectField('Općina', validators=[DataRequired()], choices=[], validate_choice=False)
    mjesto = StringField('Mjesto', validators=[DataRequired()])
    ulica = StringField('Ulica', validators=[DataRequired()])
    kbr =  StringField('Kućni broj', validators=[DataRequired()])
    
class AccountForm(FlaskForm):
    username = StringField('Korisničko ime', validators=[DataRequired()])
    type = RadioField('Vrsta',  validators=[DataRequired()], choices=[('centar','Centar'), ('opg', 'Opg')])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    oib = StringField('OIB', validators=[DataRequired(), Length(min=13, max=13)])
    adress = FormField(AdressForm)
    recaptcha = RecaptchaField()
    submit = SubmitField('Napravi korisnika')   
    def validate_username(self, username):
        user = mongo.db.users.find_one({"username": username.data})
        if user:
            raise ValidationError("Korisničko ime već postoji")     
    def validate_email(self, email):
        user = mongo.db.users.find_one({"email": email.data})
        if user:
            raise ValidationError("Email već postoji")
    def validate_oib(self, oib):
        user = mongo.db.users.find_one({"oib": oib.data})
        if user:
            raise ValidationError("OIB već postoji")
        
class MessageForm(FlaskForm):
    poruka = TextAreaField('Poruka', validators=[DataRequired()])
    submit = SubmitField('Pošalji poruku')