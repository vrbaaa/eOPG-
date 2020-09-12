from flask import render_template, url_for, flash, redirect, request, session, jsonify, Blueprint, make_response
from opghelper import app, mongo, bcrypt, io
from flask_login import login_user, current_user, logout_user
from bson.objectid import ObjectId
from datetime import datetime
import smtplib
from PIL import Image

import randomcolor
import random
import string
import os
import secrets
from flask_socketio import SocketIO, send, emit
import json
from collections import Counter, defaultdict
from functools import wraps
from opghelper.users.forms import LoginForm, adresaForm, AccountForm, MessageForm
import requests

userss = mongo.db.korisnici
products = mongo.db.proizvodi
offers = mongo.db.offers
protuponude = mongo.db.protuponude
dnevnik = mongo.db.dnevnik
protuponudeZaCentar = mongo.db.protuponudeZaCentar
oglasi = mongo.db.oglasi
poruke = mongo.db.poruke

users = Blueprint('users', __name__)
kor = {}
clients = []

# def login_required(f):
#     @wraps(f)
#     def wrap(*args, **kwargs):
#         if 'korisnicko_ime' in session:
#             return f(*args, **kwargs)
#         else:
#             flash('You need to login first.')
#             return redirect(url_for('users.index'))
#     return wrap

def save_slika(form_slika):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_slika.filename)
    slika_fn = random_hex + f_ext
    slika_path = os.path.join(app.root_path, 'static/images', slika_fn)

    output_size = (125, 125)
    i = Image.open(form_slika)
    i.thumbnail(output_size)
    i.save(slika_path)

    return slika_fn


def upisiUDnevnik(radnja):
    if (session['type'] != 'admin'):
        dnevnik.insert_one(
                            {
                                "korisnik" : session['korisnicko_ime'],
                                "radnja" : radnja,
                                "vrijeme" : datetime.now()
                            }
                        )
@users.context_processor
def context_processor():
    if 'korisnicko_ime' in session:
        broj = poruke.find({
                                    "$and": [
                                        {"primatelj" : session['korisnicko_ime']},
                                        {"procitana" : False}
                                    ]
                                }).count()
        return dict(broj=broj)  
    else:
        return dict(val="kkk")

@users.route('/', methods=['GET', 'POST'])
def index():
    if 'korisnicko_ime' in session:
        korisnicko_ime = session['korisnicko_ime']
        user = userss.find_one({'korisnicko_ime' : korisnicko_ime})
        userType = user['type']
        zaht = list(userss.find({"odbijen": False, "prihvacen" : False}))
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
            oglasii = list(oglasi.find({"prodavatelj" : session['korisnicko_ime']}, {"proizvod" : 1, "cijena" :1, "kolicina" : 1, "_id" :0}))
        if session['type'] == 'centar':
            oglasii = list(oglasi.find({"kupac_id" : session['korisnicko_ime']}, {"proizvod" : 1, "cijena" :1, "kolicina" : 1, "_id" :0}))
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
        for znak in 'Znak': 
            print(znak)
        if form.validate_on_submit():
            login_user = userss.find_one({'korisnicko_ime' : form.korisnicko_ime.data})
            if login_user and login_user['password'] == form.password.data:
                if form.korisnicko_ime.data != 'admin':
                    if login_user['blokiran']:
                        flash('Prijava neuspješna. Blokirani ste od strane administraora', 'danger')
                    else:
                        if len(login_user['ocjene']) > 2:
                            ocjena = 0
                            brojac = 0
                            ukupnaOcjena = 0
                            for x in login_user['ocjene']:
                                if x != '': 
                                    brojac = brojac + 1
                                    ukupnaOcjena += x['rating']
                            ocjena = ukupnaOcjena / brojac
                            if ocjena > 1.5:
                                session.permanent = True
                                session['korisnicko_ime'] =  form.korisnicko_ime.data
                                session['type'] = login_user['type']
                                upisiUDnevnik("Prijava u sustav")
                                flash('Prijavljeni ste.', 'success')
                                return redirect(url_for('users.index'))
                            else:
                                flash('Prijava neuspješna. Imate premalu ocjenu', 'danger')  
                        else:
                            session.permanent = True
                            session['korisnicko_ime'] =  form.korisnicko_ime.data
                            session['type'] = login_user['type']
                            upisiUDnevnik("Prijava u sustav")
                            flash('Prijavljeni ste.', 'success')
                            return redirect(url_for('users.index'))
                else: 
                        session['korisnicko_ime'] =  form.korisnicko_ime.data
                        session['type'] = login_user['type']
                        upisiUDnevnik("Prijava u sustav")
                        flash('Prijavljeni ste.', 'success')
                        return redirect(url_for('users.index'))       
            else:
                    flash('Prijava neuspješna. Nesipravno korisničko ime ili lozinka', 'danger')
                    #return render_template('index.html', form = form)
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
    form.adresa.zupanija.choices = [(x['name'], x['name']) for x in data['counties']]
    form.adresa.opcina.choices = [(x['name'], x['name']) for x in data['towns'] if x['countyName'] == 'ZAGREBAČKA']
    if(form.validate_on_submit()): 
        if form.slika.data:
            slika_file = save_slika(form.slika.data)
        else:
            slika_file = '238880ae0bcd486c.png'
        userss.insert_one({
            "korisnicko_ime" : form.korisnicko_ime.data,
            "type" : form.type.data,
            "email" : form.email.data,
            "oib" : form.oib.data,
            "adresa" : form.adresa.data,
            "ocjene": [],
            "slika" : slika_file,
            "jeZahtjev" : True,
            "odbijen" : False,
            "prihvacen" : False,
            "datumIVrijemeKreiranjaZahtjeva" : datetime.now()    
        })
        return redirect(url_for('users.index'))
    return render_template('zahtjev.html', form = form)


@users.route('/posaljiPoruku/admin', methods=['GET', 'POST'])
def porukeAdmina():
    form = MessageForm()
    c = "admin"
    por = poruke.find( {
      "$and" : [
               { 
                 "$or" : [ 
                         {"primatelj" : session['korisnicko_ime']},
                         {"posiljatelj" : session['korisnicko_ime']}
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

@users.route('/porukee', methods=['GET', 'POST'])
def porukee():
    posiljatelji = poruke.distinct(("posiljatelj"), {"primatelj": session['korisnicko_ime']}) 
    posljednjePoruke = []
    brNep = []
    for posiljatelj in posiljatelji:
        zadnjePorukePoPosiljatelju = list(poruke.find({"posiljatelj": posiljatelj,  "primatelj": session['korisnicko_ime']}).sort([("datum_slanja",  -1)]).limit(1))
        brojNeprocitanihPoKorisniku = list(poruke.aggregate([ 
                    {
                        "$match": 
                            {
                                "$and": [
                                    {"primatelj" : session['korisnicko_ime']},
                                    {"procitana" : False}, 
                                    {"posiljatelj" : posiljatelj}
                                ]
                            }
                        },
                    {"$count": posiljatelj }
                    ]))
        posljednjePoruke.append(zadnjePorukePoPosiljatelju)
        brNep.append(brojNeprocitanihPoKorisniku)
        print(brojNeprocitanihPoKorisniku)
    print(brNep)
    return render_template('poruke.html', posljednjePoruke = posljednjePoruke, brNep = brNep)
