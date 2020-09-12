from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, IntegerField, FloatField, RadioField, DateField, SubmitField, PasswordField, FieldList, FormField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from opghelper import  mongo

class LoginForm(FlaskForm):
    korisnicko_ime = StringField('Korisničko ime', validators=[DataRequired()])
    password = PasswordField('Lozinka')
    submit = SubmitField('Prijavi se')   

class adresaForm(FlaskForm):
    zupanija = SelectField('Županija', validators=[DataRequired()], choices=[])
    opcina = SelectField('Općina', validators=[DataRequired()], choices=[], validate_choice=False)
    mjesto = StringField('Mjesto', validators=[DataRequired()])
    ulica = StringField('Ulica', validators=[DataRequired()])
    kbr =  StringField('Kućni broj', validators=[DataRequired()])
    
class AccountForm(FlaskForm):
    korisnicko_ime = StringField('Korisničko ime', validators=[DataRequired()])
    type = RadioField('Vrsta',  validators=[DataRequired()], choices=[('centar','Centar'), ('opg', 'Opg')])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    oib = StringField('OIB', validators=[DataRequired(), Length(min=13, max=13)])
    adresa = FormField(adresaForm)
    slika = FileField('Profilna slika', validators=[FileAllowed(['jpg', 'png'])])
    recaptcha = RecaptchaField()
    submit = SubmitField('Napravi korisnika')   
    def validate_korisnicko_ime(self, korisnicko_ime):
        user = mongo.db.korisnici.find_one({"korisnicko_ime": korisnicko_ime.data})
        if user:
            raise ValidationError("Korisničko ime već postoji")     
    def validate_email(self, email):
        user = mongo.db.korisnici.find_one({"email": email.data})
        if user:
            raise ValidationError("Email već postoji")
    def validate_oib(self, oib):
        user = mongo.db.korisnici.find_one({"oib": oib.data})
        if user:
            raise ValidationError("OIB već postoji")
        
class MessageForm(FlaskForm):
    poruka = TextAreaField('Poruka', validators=[DataRequired()])
    submit = SubmitField('Pošalji poruku')