from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, IntegerField, FloatField, RadioField, DateField, SubmitField, PasswordField, FieldList, FormField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from opghelper import  mongo

class adresaForm(FlaskForm):
    zupanija = SelectField('Županija', validators=[DataRequired()], choices=[], validate_choice=False)
    opcina = SelectField('Općina', validators=[DataRequired()], choices=[], validate_choice=False)
    mjesto = StringField('Mjesto', validators=[DataRequired()])
    ulica = StringField('Ulica', validators=[DataRequired()])
    kbr =  StringField('Kućni broj', validators=[DataRequired()])
    
class UserForm(FlaskForm):
    korisnicko_ime = StringField('Korisničko ime', validators=[DataRequired()])
    password = PasswordField('Lozinka', validators=[DataRequired()])
    type = RadioField('Tip korisnika',  validators=[DataRequired()], choices=[('centar','Centar'), ('opg', 'Opg')])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    oib = StringField('OIB', validators=[DataRequired(), Length(min=13, max=13)])
    adresa = FormField(adresaForm)
    slika = FileField('Profilna slika', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Napravi korisnika')   
    def validate_korisnicko_ime(self, korisnicko_ime):
        user = mongo.db.korisnici.find_one({"korisnicko_ime": korisnicko_ime.data})
        if user:
            raise ValidationError("Korisničko ime već postoji")     
    def validate_email(self, email):
        user = mongo.db.korisnici.find_one({"email": email.data})
        if user:
            raise ValidationError("Email ime već postoji")
        
class ProductForm(FlaskForm):
    naziv = StringField('Naziv proizvoda', validators=[DataRequired()])
    slika = StringField('Slika proizvoda', validators=[DataRequired()])
    tip = RadioField('Vrsta proizvoda',  validators=[DataRequired()], choices=[('voće','Voće'), ('povrće', 'Povrće')])
    
    def validate_name(self, naziv):
        product = mongo.db.proizvodi.find_one({"naziv": naziv.data})
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
    adresa = FormField(adresaForm)
    slika = FileField('Profilna slika', validators=[FileAllowed(['jpg', 'png'])])
    blokiran = BooleanField('Blokiran')
    submit = SubmitField('Ažuriraj korisnika')     
    # def validate_email(self, email):
    #     user = mongo.db.users.find_one({"email": email.data})
    #     if user:
    #         raise ValidationError("Email ime već postoji")