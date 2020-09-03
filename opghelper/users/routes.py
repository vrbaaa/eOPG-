from flask import render_template, url_for, flash, redirect, request, session, jsonify, Blueprint
from opghelper import app, mongo, bcrypt, io
from flask_login import login_user, current_user, logout_user
from bson.objectid import ObjectId
from datetime import datetime
import smtplib
import randomcolor
import random
import string
from flask_socketio import SocketIO, send, emit
import json
from collections import Counter, defaultdict
from functools import wraps
from opghelper.users.forms import LoginForm, AdressForm, AccountForm, MessageForm
import requests

userss = mongo.db.users
products = mongo.db.products
offers = mongo.db.offers
protuponude = mongo.db.protuponude
dnevnik = mongo.db.dnevnik
protuponudeZaCentar = mongo.db.protuponudeZaCentar
oglasi = mongo.db.oglasi
zahtjevi = mongo.db.zahtjevi
poruke = mongo.db.poruke

users = Blueprint('users', __name__)
kor = {}
clients = []

# def login_required(f):
#     @wraps(f)
#     def wrap(*args, **kwargs):
#         if 'username' in session:
#             return f(*args, **kwargs)
#         else:
#             flash('You need to login first.')
#             return redirect(url_for('users.index'))
#     return wrap

def upisiUDnevnik(radnja):
    if (session['type'] != 'admin'):
        dnevnik.insert_one(
                            {
                                "korisnik" : session['username'],
                                "radnja" : radnja,
                                "vrijeme" : datetime.now()
                            }
                        )

@users.route('/', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        username = session['username']
        user = userss.find_one({'username' : username})
        userType = user['type']
        zaht = list(zahtjevi.find({"odbijen": False, "prihvacen" : False}))
        session['brojZahtjeva'] = len(zaht)
        novac = 0
        brojac = 0
        boje = 0
        array = []
        arod = []
        labels = []
        values = []
        kol = []
        uk = []
        colors = ['#C7980A', '#F4651F', '#82D8A7', '#CC3A05']
        if session['type'] == 'opg':
            oglasii = list(oglasi.find({"prodavatelj" : session['username']}, {"proizvod" : 1, "cijena" :1, "kolicina" : 1, "_id" :0}))
        if session['type'] == 'centar':
            oglasii = list(oglasi.find({"kupac_id" : session['username']}, {"proizvod" : 1, "cijena" :1, "kolicina" : 1, "_id" :0}))
        if session['type'] == 'admin':
            oglasii = list(oglasi.find({"kupljen" : True}, {"proizvod" : 1, "cijena" :1, "kolicina" : 1, "_id" :0}))
        for oglas in oglasii:
            arod.append(oglas)
            array.append(oglas['proizvod'])
            novac += (float(oglas['cijena']) * float(oglas['kolicina']))
            brojac += 1
        dictOfElems = dict(Counter(array))
        dictOfElems = { key:value for key, value in dictOfElems.items()}
        for key, value in dictOfElems.items():
            labels.append(key)
            values.append(value)
            boje += 1
        c = defaultdict(float)
        for d in arod:
            c[d['proizvod']] += d['kolicina']
        for proizvod, kolicina in c.items():
            kol.append(kolicina)
        e = defaultdict(float)
        for d in arod:
            e[d['proizvod']] += d['kolicina']*float(d['cijena'])
        for proizvod, kolicina in e.items():
            uk.append(kolicina)
        rand_color = randomcolor.RandomColor()
        cols = (rand_color.generate(count=boje))
        print(clients)
        return render_template('frontpage.html', type=userType, novac = novac, brojac = brojac, dict=dictOfElems, set=zip(values, labels, cols), labels=labels, values = kol, uk = uk)
    else:
        form = LoginForm()
        if form.validate_on_submit():
            login_user = userss.find_one({'username' : form.username.data})
            if login_user and login_user['password'] == form.password.data:
                if form.username.data != 'admin':
                    if len(login_user['ratings']) > 2:
                        ocjena = 0
                        brojac = 0
                        ukupnaOcjena = 0
                        for x in login_user['ratings']:
                            if x != '': 
                                brojac = brojac + 1
                                ukupnaOcjena += x['rating']
                        ocjena = ukupnaOcjena / brojac
                        if ocjena > 1.5:
                            session.permanent = True
                            session['username'] =  form.username.data
                            session['type'] = login_user['type']
                            upisiUDnevnik("Prijava u sustav")
                            flash('Prijavljeni ste.', 'success')
                            return redirect(url_for('users.index'))
                        else:
                            flash('Prijava neuspješna. Imate premalu ocjenu', 'danger')  
                    else:
                        session.permanent = True
                        session['username'] =  form.username.data
                        session['type'] = login_user['type']
                        upisiUDnevnik("Prijava u sustav")
                        flash('Prijavljeni ste.', 'success')
                        return redirect(url_for('users.index'))
                else: 
                    session['username'] =  form.username.data
                    session['type'] = login_user['type']
                    upisiUDnevnik("Prijava u sustav")
                    flash('Prijavljeni ste.', 'success')
                    return redirect(url_for('users.index'))       
            else:
                flash('Prijava neuspješna. Nesipravno korisničko ime ili lozinka', 'danger')
        return render_template('index.html', form = form)

@users.route('/logout')
def logout():
    upisiUDnevnik("Odjava iz sustava")
    session.clear()
    flash('Odjava')
    return redirect(url_for('users.index'))

@users.route('/zahtjev', methods=['GET', 'POST'])
def zahtjev():
    req = requests.get('https://tehcon.com.hr/api/CroatiaTownAPI/list.php')
    data = json.loads(req.content)
    form = AccountForm()
    form.adress.zupanija.choices = [(x['name'], x['name']) for x in data['counties']]
    form.adress.opcina.choices = [(x['name'], x['name']) for x in data['towns'] if x['countyName'] == 'ZAGREBAČKA']
    if(form.validate_on_submit()): 
        zahtjevi.insert_one({
            "username" : form.username.data,
            "type" : form.type.data,
            "email" : form.email.data,
            "oib" : form.oib.data,
            "adress" : form.adress.data,
            "odbijen" : False,
            "prihvacen" : False,
            "datumIVrijemeKreiranja" : datetime.now()    
        })
        return redirect(url_for('users.index'))
    return render_template('zahtjev.html', form = form)


@users.route('/porukeAdmina', methods=['GET', 'POST'])
def porukeAdmina():
    form = MessageForm()
    c = "admin"
    por = poruke.find( {
      "$and" : [
               { 
                 "$or" : [ 
                         {"primatelj" : session['username']},
                         {"posiljatelj" : session['username']}
                       ]
               },
                 { 
                 "$or" : [ 
                         {"primatelj" : c},
                         {"posiljatelj" : c}
                       ]
               }
             ]
    })
    return render_template("novaPoruka.html", form = form, centar = c, poruke = por)

