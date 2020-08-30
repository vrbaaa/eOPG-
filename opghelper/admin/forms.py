from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, IntegerField, FloatField, RadioField, DateField, SubmitField, PasswordField, FieldList, FormField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from opghelper import  mongo

class AdressForm(FlaskForm):
    zupanija = SelectField('Županija', validators=[DataRequired()], choices=[], validate_choice=False)
    opcina = SelectField('Općina', validators=[DataRequired()], choices=[], validate_choice=False)
    mjesto = StringField('Mjesto', validators=[DataRequired()])
    ulica = StringField('Ulica', validators=[DataRequired()])
    kbr =  StringField('Kućni broj', validators=[DataRequired()])
    
class UserForm(FlaskForm):
    username = StringField('Korisničko ime', validators=[DataRequired()])
    password = PasswordField('Lozinka', validators=[DataRequired()])
    type = RadioField('Tip korisnika',  validators=[DataRequired()], choices=[('centar','Centar'), ('opg', 'Opg')])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    oib = StringField('OIB', validators=[DataRequired(), Length(min=13, max=13)])
    adress = FormField(AdressForm)
    picture = FileField('Profilna slika', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Napravi korisnika')   
    def validate_username(self, username):
        user = mongo.db.users.find_one({"username": username.data})
        if user:
            raise ValidationError("Korisničko ime već postoji")     
    def validate_email(self, email):
        user = mongo.db.users.find_one({"email": email.data})
        if user:
            raise ValidationError("Email ime već postoji")
        
class ProductForm(FlaskForm):
    name = StringField('Naziv proizvoda', validators=[DataRequired()])
    type = RadioField('Vrsta proizvoda',  validators=[DataRequired()], choices=[('voće','Voće'), ('povrće', 'Povrće')])
    
    def validate_name(self, name):
        product = mongo.db.products.find_one({"name": name.data})
        if product:
            raise ValidationError("Ovaj proizvod već postoji")
        
class OglasForm(FlaskForm):
    naziv = StringField('Naziv')
    objavio = SelectField('Korisnik za kojeg se objavljuje oglas ')
    proizvod = SelectField('Proizvod')
    cijena = FloatField('Cijena', validators=[DataRequired()])
    kolicina = FloatField('Kolicina', validators=[DataRequired()])
    prijevoz = RadioField('Prijevoz',  validators=[DataRequired()], choices=[('centar','Centar'), ('opg', 'Opg')])
    datumDostave = DateField('Datum dostave', validators=[DataRequired()], format='%d.%m.%Y.')
    submit = SubmitField('Dodaj novi oglas')
    

class MessageForm(FlaskForm):
    poruka = TextAreaField('Poruka', validators=[DataRequired()])
    submit = SubmitField('Pošalji poruku')


class UserUpdateForm(FlaskForm):
    type = RadioField('Tip korisnika',  validators=[DataRequired()], choices=[('centar','Centar'), ('opg', 'Opg')])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    oib = StringField('OIB', validators=[DataRequired(), Length(min=13, max=13)])
    adress = FormField(AdressForm)
    picture = FileField('Profilna slika', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Ažuriraj korisnika')     
    # def validate_email(self, email):
    #     user = mongo.db.users.find_one({"email": email.data})
    #     if user:
    #         raise ValidationError("Email ime već postoji")