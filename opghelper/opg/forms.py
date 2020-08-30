from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, FloatField, RadioField, DateField, SubmitField, PasswordField, FieldList, FormField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, ValidationError, NumberRange
from opghelper import  mongo

class OglasForm(FlaskForm):
    naziv = StringField('Naziv')
    proizvod = SelectField('Proizvod')
    cijena = FloatField('Cijena', validators=[DataRequired()])
    kolicina = FloatField('Kolicina', validators=[DataRequired()])
    prijevoz = RadioField('Prijevoz',  validators=[DataRequired()], choices=[('centar','Centar'), ('opg', 'Opg')])
    datumDostave = DateField('Datum dostave', validators=[DataRequired()], format='%d.%m.%Y.')
    submit = SubmitField('Dodaj novi oglas')

class OcjenaForm(FlaskForm):
    ocjena = IntegerField('Ocjena od 1 do 5', validators=[DataRequired(), NumberRange(min=1, max=5, message="Ocjena mora biti od 1 do 5")])
    submit = SubmitField('Ocjeni korisnika')

class MessageForm(FlaskForm):
    poruka = TextAreaField('Poruka', validators=[DataRequired()])
    submit = SubmitField('Pošalji poruku')