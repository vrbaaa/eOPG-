from flask import render_template, url_for, flash, redirect, request, session, jsonify, Blueprint
from PIL import Image
from opghelper import app, mongo, bcrypt
from functools import wraps
from flask_login import login_user, current_user, logout_user
from bson.objectid import ObjectId
from datetime import datetime
import smtplib
import random
import string
import os
import secrets
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
from opghelper.admin.forms import  UserForm, adresaForm, ProductForm, OglasForm,MessageForm, UserUpdateForm


import randomcolor


import json
from collections import Counter, defaultdict
import requests
users = mongo.db.korisnici
products = mongo.db.proizvodi
protuponude = mongo.db.protuponude
protuponudeZaCentar = mongo.db.protuponudeZaCentar
oglasi = mongo.db.oglasi
dnevnik = mongo.db.dnevnik
poruke = mongo.db.poruke
zahtjevi = mongo.db.zahtjevi

admin = Blueprint('admin', __name__)

def myFunc(e):
  return e['total']

def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'korisnicko_ime' in session:
            return test(*args, **kwargs)
        else:
            flash('Morate se prijaviti')
            return redirect(url_for('users.index'))
    return wrap

def getPassword(letters_count, digits_count):
    sample_str = ''.join((random.choice(string.ascii_letters) for i in range(letters_count)))
    sample_str += ''.join((random.choice(string.digits) for i in range(digits_count)))

    sample_list = list(sample_str)
    random.shuffle(sample_list)
    final_string = ''.join(sample_list)
    return final_string

def getOpcine(zupanija):
    urlf = 'http://localhost:5000/opcina/'
    url = f"{urlf}{zupanija}"
    r = requests.get(url)
    re = r.json()
    return re['gradoviopcine']
    
def indexOfElem(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None

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

@admin.route('/admin_dodaj_korisnika', methods=['GET', 'POST'])
def admin_dodaj_korisnika():
    if (session['type'] == 'admin'):
        req = requests.get('https://tehcon.com.hr/api/CroatiaTownAPI/list.php')
        data = json.loads(req.content)
        form = UserForm()
        form.adresa.zupanija.choices = [(x['name'], x['name']) for x in data['counties']]
        if form.validate_on_submit():
            if form.slika.data:
                slika_file = save_slika(form.slika.data)
            else:
                slika_file = '238880ae0bcd486c.png'
            users.insert_one({
                "korisnicko_ime" : form.korisnicko_ime.data,
                "password" : form.password.data,
                "type" : form.type.data,
                "email" : form.email.data,
                "oib" : form.oib.data,
                "adresa" : form.adresa.data,
                "datumIVrijemeKreiranja" : datetime.now(),
                "slika" : slika_file,
                "ocjene" : [],
                "jeZahtjev" : False,
                "blokiran": False
            })
            print(form.errors)
            flash('Unijeli ste uspješno novog korisnika!', 'success')
            return redirect(url_for('admin.admin_popis_korisnika'))
        print(form.errors)
        return render_template("admin_dodaj_korisnika.html", form=form)

@admin.route('/opcina/<string:zupanija>')
def opcina(zupanija):
    req = requests.get('https://tehcon.com.hr/api/CroatiaTownAPI/list.php')
    data = json.loads(req.content)
    gradoviIOpcine = []
    for x in data['towns']:
        if x['countyName'] == zupanija:
            gradoviObj = {}
            gradoviObj['id'] = x['name']
            gradoviObj['name'] = x['name']
            gradoviIOpcine.append(gradoviObj)
            
    for x in data['communities']:
        if x['countyName'] == zupanija:
            opcineObj = {}
            opcineObj['id'] = x['name']
            opcineObj['name'] = x['name']
            gradoviIOpcine.append(opcineObj)
    
    return jsonify ({'gradoviopcine' : gradoviIOpcine})

@admin.route('/admin_popis_korisnika')
@login_required
def admin_popis_korisnika():
        centri = list(users.find(
            { "$and": 
                 [
                    { 
                        "$or" :
                        [ 
                            {
                                "jeZahtjev" : False
                            },
                            {
                               "$and" : 
                                   [
                                        {"jeZahtjev" : True},
                                        {"prihvacen" : True}
                                    ]
                            }
                        ]
                    }, 
                    { 
                        "type" : {"$ne" : "admin"}
                    }
                 ]
            }))
                         
        ocjene = {}
        ocjena = []
        try: 
            for centar in centri:
                useri = []
                ocjene['id'] = centar['_id']
                ocjene['korisnicko_ime'] = centar['korisnicko_ime']
                ukupnaOcjena = 0
                ocjene['avg'] = 0
                brojac = 0
                brojOcjena = len(centar['ocjene'])
                for x in centar['ocjene']:
                    if x != '': 
                        brojac = brojac + 1
                        ukupnaOcjena += x['rating']
                        ocjene['avg'] = ukupnaOcjena / brojac
                        useri.append(x['user_id'])
                    else:
                        ocjene['avg'] = 'Nema ocjena za opg'
                ocjene['useri'] = useri
                ocjena.append(dict(ocjene))
        except Exception as ex: 
            print(ex)
        print(ocjena)
        print(centri)
        return render_template ('admin_popis_korisnika.html',centri = centri, ja = session['korisnicko_ime'], ocjene = ocjena)

@admin.route('/admin_proizvodi', methods=['GET', 'POST'])
def admin_proizvodi():
    if (session['type'] == 'admin'):
        proizvodi = products.find()
        proizz = list(products.find({}, {"_id": 0, "naziv" : 1}))
        kupljeniProizvodi = []
        producti = list(oglasi.aggregate([
                        { "$match": { "kupljen" : True } },
                        { "$group": { "_id": "$proizvod", "total": { "$sum": "$kolicina" } } },
                        { "$sort": { "total": -1 } }
                        ]))
        form = ProductForm()
        print(form.errors)
        for p in producti:
            kupljeniProizvodi.append(p['_id'])
        if form.validate_on_submit():
            products.insert_one({
                "naziv" : form.naziv.data,
                "tip": form.tip.data,
                "slika": form.slika.data
            })
            
            flash ('Dodali ste novi proizvod', 'success')
            return render_template ('admin_proizvodi.html', proizvodi = proizvodi, form = form, producti = producti, proizz=proizz, kupljeniProizvodi = kupljeniProizvodi)
        print(form.errors)
        print(request.args)
        return render_template ('admin_proizvodi.html', proizvodi = proizvodi, form = form, producti = producti, proizz=proizz, kupljeniProizvodi = kupljeniProizvodi)
        
@admin.route('/pr', methods=['GET', 'POST'])
def pr():
    form = ProductForm()
    if form.validate_on_submit():
            products.insert_one({
                "naziv" : form.naziv.data,
                "tip": form.tip.data,
                "slika" : form.slika.data
            })
            flash ('Dodali ste novi proizvod', 'success')
            return render_template('proizvodi.html', form=form)
    return render_template('proizvodi.html', form=form)

@admin.route('/proizvodi', methods=['GET'])
def json_proizvodi():
        jsonOutput = []
        for p in products.find():
            jsonOutput.append({
                    "id" : str(ObjectId(p['_id'])),
                    "naziv" : p['naziv'],
                    "tip" : p['tip'], 
                    "slika" : p['slika'], 
                    "total" : 0                
                })
        producti = list(oglasi.aggregate([
                            { "$match": { "kupljen" : True } },
                            { "$group": { "_id": "$proizvod", "total": { "$sum": "$kolicina" } } },
                            { "$sort": { "total": -1 } }
                            ]))
        for pr in producti:
            for p in jsonOutput:
                if (pr['_id'] == p['naziv']):
                    ind = indexOfElem(jsonOutput, 'naziv', p['naziv'])
                    jsonOutput[ind]['total'] = pr['total']
        jsonOutput.sort(reverse=True, key=myFunc)
        return jsonify({'result' : jsonOutput})

        
@admin.route('/proizvodi', methods=['POST'])
def dodaj_proizvod():
    naziv = request.json['naziv']
    tip = request.json['tip']
    slika = request.json['slika']
        
    proizvod_id = products.insert({"naziv" : naziv, "tip" : tip, "slika" : slika})  
    novi_proizvod = products.find_one({"_id" : proizvod_id})
        
    output = {'naziv' : novi_proizvod['naziv'], 'tip' : novi_proizvod['tip']}
        
    return jsonify({'result' : output})

@admin.route('/proizvodi/<string:naziv>', methods=['PUT'])
def azuriraj_proizvod(naziv):
    az_proizvod = products.update_one({"naziv" : naziv},
                                   {"$set" : {
                                       "naziv" :  request.json['naziv'],
                                       "tip" :  request.json['tip'],
                                       "slika" :  request.json['slika'],
                                   }})
    
    novi_proizvod = products.find_one({"naziv" : request.json['naziv']})
    
    output = {'naziv' : novi_proizvod['naziv'], 'tip' : novi_proizvod['tip']}
    
    return jsonify({'result' : output})

@admin.route('/proizvodi/<string:naziv>', methods=['DELETE'])
def obrisi_proizvod(naziv):
    products.delete_one({"naziv" : naziv})
    
    return redirect(url_for('admin.json_proizvodi'))

            
@admin.route('/uredi_proizvod/<string:pid>', methods=['GET', 'POST'])
def uredi_proizvod(pid):
     if request.method == 'POST': 
            products.update_one({"_id" : ObjectId(pid)}, 
                            {"$set" :
                            {
                                "naziv" : request.form.get('naziv'),
                                "tip" : request.form.get('vrsta'),
                                "slika" : request.form.get('slika'),
                            }
                            })
            flash('Uspješno ste ažurirali proizvod!', 'success')
            return redirect(url_for('admin.pr'))

@admin.route('/korisnik/<string:korisnik>/<string:tip>')
def korisnik(korisnik, tip):
    if (session['type'] == 'admin'):
        try:
            if tip == 'opg':
                oglasii = list(oglasi.find({"prodavatelj" : korisnik}, {"proizvod" : 1, "cijena" :1, "kolicina" : 1, "_id" :0}))
            else:
                oglasii = list(oglasi.find({"kupac_id" : korisnik}, {"proizvod" : 1, "cijena" :1, "kolicina" : 1, "_id" :0}))
        except: 
            print('Greška')
        
        novac = 0
        brojac = 0
        boje = 0
        array = []
        arod = []
        labels = []
        values = []
        kol = []
        uk = []
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
        return render_template('admin_korisnik.html', korisnik = korisnik, tip=tip, novac = novac, brojac = brojac, dict=dictOfElems, set=zip(values, labels, cols), labels=labels, values = kol, uk = uk, oglasi=oglasii)
    
@admin.route('/dnevnik')
def admin_dnevnik():
    rad = 'Sve radnje'
    kor = 'Svi korisnici'
    dne = dnevnik.find()
    radnje = list(dnevnik.distinct(("radnja"),{}))
    korisnici = users.find({"type" : {"$ne": "admin"}})
    return render_template('dnevnik.html', dnevnik = dne, radnje = radnje, korisnici = korisnici, rad = rad, kor = kor)

@admin.route('/statistika_dnevnik_korisnik')
def statistika_dnevnik_korisnik():
    kor = 'OPG Završni rad'
    radnje = list(dnevnik.distinct(("radnja"),{}))
    korisnici = users.find({"type" : {"$ne": "admin"}})
    dnevnikResults = list(dnevnik.aggregate
                  ([ 
                    {"$match": {"korisnik" : kor}},
                    {"$group": {  "_id": "$radnja", "total": {"$sum": 1} }},
                    {"$sort": { "total": -1 }}
                    ]))
    return render_template('dnevnik_korisnik.html', dnevnik = dnevnikResults, radnje = radnje, korisnici = korisnici, kor = kor)

@admin.route('/statistika_dnevnik_radnje')
def statistika_dnevnik_radnje():
    rad = 'Prijava u sustav'
    radnje = list(dnevnik.distinct(("radnja"),{}))
    korisnici = users.find({"type" : {"$ne": "admin"}})
    dnevnikResults = list(dnevnik.aggregate
                  ([ 
                    {"$match": {"radnja" : rad}},
                    {"$group": {  "_id": "$korisnik", "total": {"$sum": 1} }},
                    {"$sort": { "total": -1 }}
                    ]))
    return render_template('dnevnik_radnje.html', dnevnik = dnevnikResults, radnje = radnje, korisnici = korisnici, rad =  rad)

@admin.route('/aktivniOglasi')
def aktivniOglasi():
        oglasResults = list(oglasi.find({"kupljen" : False}))
        productsResults = list(products.find({}))
        usersResults = users.find({})
        tip = []
        return render_template("admin_aktivni_oglasi.html", oglasi = oglasResults, users = usersResults, products = productsResults)

@admin.route('/admin_search')
def admin_search():
        rad = 'Sve radnje'
        kor = 'Svi korisnici'        
        radnje = list(dnevnik.distinct(("radnja"),{}))
        korisnici = users.find({"type" : {"$ne": "admin"}})
        radnja = request.args.get('radnja')
        korisnik = request.args.get('korisnik')
        if radnja == 'Sve radnje' and korisnik != 'Svi korisnici':  
            dnevnikResults = dnevnik.find({"korisnik" : korisnik})
        elif radnja != 'Sve radnje' and korisnik != 'Svi korisnici':
            dnevnikResults = dnevnik.find({"korisnik" : korisnik, "radnja" : radnja})
        elif  radnja != 'Sve radnje' and korisnik == 'Svi korisnici':
            dnevnikResults = dnevnik.find({"radnja" : radnja})
        elif radnja == 'Sve radnje' and korisnik == 'Svi korisnici':
            dnevnikResults = dnevnik.find()
        return render_template('dnevnik.html', dnevnik = dnevnikResults, radnje = radnje, korisnici = korisnici, rad = radnja, kor = korisnik)
    
@admin.route('/admin_search_korisnik')
def admin_search_korisnik():
        kor = 'OPG Završni rad'        
        korisnici = users.find({"type" : {"$ne": "admin"}})
        korisnik = request.args.get('korisnik')  
        dnevnikResults = list(dnevnik.aggregate
                  ([ 
                    {"$match": {"korisnik" : korisnik}},
                    {"$group": {  "_id": "$radnja", "total": {"$sum": 1} }},
                    {"$sort": { "total": -1 }}
                    ]))
        return render_template('dnevnik_korisnik.html', dnevnik = dnevnikResults, korisnici = korisnici, kor = korisnik)
    
@admin.route('/admin_search_radnja')
def admin_search_radnja():
        rad = 'Prijava u sustav'        
        radnje = list(dnevnik.distinct(("radnja"),{}))
        radnja = request.args.get('radnja')  
        dnevnikResults = list(dnevnik.aggregate
                  ([ 
                    {"$match": {"radnja" : radnja}},
                    {"$group": {  "_id": "$korisnik", "total": {"$sum": 1} }},
                    {"$sort": { "total": -1 }}
                    ]))
        return render_template('dnevnik_radnje.html', dnevnik = dnevnikResults, radnje = radnje, rad = rad)

@admin.route('/admin_dodaj_oglas', methods=['GET', 'POST'])  
def admin_dodaj_oglas():
        form = OglasForm()
        tip = []
        form.proizvod.choices = [(proizvod['naziv'], proizvod['naziv']) for proizvod in products.find({})]
        form.objavio.choices = [(kor['korisnicko_ime'], kor['korisnicko_ime']) for kor in users.find({"type": {"$ne" : "admin"}})]
        print(form.errors)
        if form.validate_on_submit():    
            objavioArray = list(users.find({"korisnicko_ime" : form.objavio.data}, {"type" : 1, "_id" : 0}))
            for a in objavioArray:
                tip.append(a['type'])    
            oglasi.insert_one({
                "objavio" : form.objavio.data,
                "naziv" : form.naziv.data,
                "cijena" : form.cijena.data,
                "kolicina" : form.kolicina.data,
                "prijevoz" : form.prijevoz.data,
                "proizvod" : form.proizvod.data,
                "datumDostave" : datetime.strptime(str(form.datumDostave.data), '%Y-%m-%d'),
                "datumIVrijemeObjavljivanja" : datetime.now(),
                "zatvoren" : False,
                "kupljen" : False,
                "tipObjavio" : tip[0]
            })
            flash('Objavili ste uspješno novi oglas!', 'success')
            # ogl = oglasi.distinct("objavio", {"kupljen" : False, "tipObjavio" : "opg", "proizvod" : form.proizvod.data, "kolicina" : {"$lte" : form.kolicina.data}})
            # for og in ogl:
            #     us = list(users.find({"korisnicko_ime" : og}))
            #     message = "Centar " + session['korisnicko_ime'] + "je objavio oglas za proizvod " + form.proizvod.data +" Kolicina : " + str(form.proizvod.data) +" Cijena " + str(form.cijena.data) +" kn. Posaljite mu poruku preko sustava i dogovorite kupnju proizvoda."
            #     msg = message.encode('utf-8')
            #     server  = smtplib.SMTP("smtp.gmail.com", 587)
            #     server.starttls()
            #     server.login("opg.aplikacija@gmail.com", "ZavrsniRadFoi2020")
            #     server.sendmail("opg.aplikacija@gmail.com", us[0]['email'], msg)
            return redirect(url_for('admin.aktivniOglasi'))
        else:
            print(form.errors)
        return render_template('admin_dodaj_oglas.html', form=form)
    
@admin.route('/posaljiPoruku/<string:korisnik>', methods=['GET', 'POST'])
def posaljiPoruku(korisnik):
    form = MessageForm()
    c = korisnik
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
                         {"primatelj" : korisnik},
                         {"posiljatelj" : korisnik}
                       ]
               }
             ]
    })
    return render_template("novaPoruka.html", form = form, centar = c, poruke = por)

@admin.route('/zahtijevi')
def zahtijevi():
    zaht = list(users.find({"jeZahtjev": True, "prihvacen" : False, "odbijen": False}))
    session['brojZahtjeva'] = len(zaht)
    return render_template('zahtjevi.html', zahtjevi = zaht)

@admin.route('/prihvatiZahtjev/<string:zahtjev_id>', methods=['GET', 'POST'])
def prihvatiZahtjev(zahtjev_id):
    zaht = users.find_one({"_id" : ObjectId(zahtjev_id)})
    lozinka = getPassword(5,3)
    users.update_one({"_id" : ObjectId(zahtjev_id)}, 
                     {"$set" : 
                         {"prihvacen" : True,
                        "password" : lozinka,
                        "blokiran" : False
                        }})
    message = "Vaš zahtjev za izradom korisničko računa na aplikaciji eOPG je odobren. Vaša lozinka je " + lozinka + ". Sada možete koristit sustav" 
    msg = message.encode('utf-8')
    server  = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("opg.aplikacija@gmail.com", "ZavrsniRadFoi2020")
    server.sendmail("opg.aplikacija@gmail.com", zaht['email'], msg)
    return redirect(url_for('admin.admin_popis_korisnika'))

@admin.route('/odbijZahtjev/<string:zahtjev_id>', methods=['GET', 'POST'])
def odbijZahtjev(zahtjev_id):
    users.update_one({"_id" : ObjectId(zahtjev_id)}, {"$set" : {"odbijen" : True}})
    return redirect(url_for('admin.zahtijevi'))

@admin.route('/racun/<string:user>', methods=['GET', 'POST'])
def racun(user):
    form = UserUpdateForm()
    trenutni_korisnik = users.find_one({"_id" : ObjectId(user)})
    korisnicko_ime= trenutni_korisnik['korisnicko_ime']
    ovaopcina = trenutni_korisnik['adresa']['opcina']
    print(form.errors)
    if form.validate_on_submit():
        if form.slika.data:
            slika = save_slika(form.slika.data)
        else:
            slika = trenutni_korisnik['slika']
        users.update_one({"_id" : ObjectId(user)},
                          {"$set" : 
                              { "type" : form.type.data,
                                "email" : form.email.data,
                                "oib" : form.oib.data,
                                "adresa" : form.adresa.data,
                                "datumIVrijemeAzuriranja" : datetime.now(),
                                "slika" : slika,
                                "blokiran" : form.blokiran.data
                              }
                            }
                          )
        print(form.errors)
        flash('Kreirali ste uspješno novog korisnika!', 'success')
        return redirect(url_for('admin.admin_popis_korisnika'))
    print(trenutni_korisnik['adresa']['zupanija'])
    form.type.data = trenutni_korisnik['type']
    form.email.data = trenutni_korisnik['email']
    form.oib.data = trenutni_korisnik['oib']
    req = requests.get('https://tehcon.com.hr/api/CroatiaTownAPI/list.php')
    data = json.loads(req.content)
    form.adresa.zupanija.process_data(trenutni_korisnik['adresa']['zupanija'].upper())
    form.adresa.zupanija.choices = [(x['name'], x['name']) for x in data['counties']]
    # form.adresa.opcina.process_data(trenutni_korisnik['adresa']['opcina'])
        # form.adresa.opcina.choices = [(x['name'], x['name']) for x in getOpcine(trenutni_korisnik['adresa']['zupanija'].upper())]
        # form.adresa.zupanija.data = trenutni_korisnik['adresa']['zupanija']
        # form.adresa.opcina.data = trenutni_korisnik['adresa']['opcina']
    form.adresa.mjesto.data = trenutni_korisnik['adresa']['mjesto']
    form.adresa.ulica.data = trenutni_korisnik['adresa']['ulica']
    form.adresa.kbr.data = trenutni_korisnik['adresa']['kbr']
    if trenutni_korisnik['slika']:
        image_file = url_for('static', filename='images/' + trenutni_korisnik['slika'])
    else:
        image_file = None
    print(form.errors)
    return render_template('racun.html', form = form, korisnicko_ime = korisnicko_ime, ovaopcina = ovaopcina, image_file=image_file)
    
@admin.route('/admin_povijestProdaje')
def admin_povijestProdaje():
    korisnici = users.find({"type" : "centar"}, {"korisnicko_ime" : 1, "_id" : 0})
    oglasiResults = oglasi.find({"kupljen" : True})
    proizvod = 'Svi proizvodi'
    korisnik = 'Svi korisnici'
    proizvodi = products.find({})
    proizvod = request.get_data().decode('UTF-8')
    return render_template("admin_povijestProdaje.html", proizvodi = proizvodi, korisnici = korisnici, oglasi = oglasiResults, pro = proizvod, kor = korisnik)


@admin.route('/povSearch')
def povSearch():
        pro = 'Svi proizvodi'
        kor = 'Svi korisnici'        
        proizvodi = products.find({})
        korisnici = users.find({"type" : "centar"}, {"korisnicko_ime" : 1, "_id" : 0})
        proizvod = request.args.get('proizvod')
        korisnik = request.args.get('korisnik')
        if proizvod == 'Svi proizvodi' and korisnik != 'Svi korisnici':  
            oglasiResults = oglasi.find({"kupac_id" : korisnik})
        elif proizvod != 'Svi proizvodi' and korisnik != 'Svi korisnici':
            oglasiResults = oglasi.find({"kupac_id" : korisnik, "proizvod" : proizvod})
        elif  proizvod != 'Svi proizvodi' and korisnik == 'Svi korisnici':
            oglasiResults = oglasi.find({"proizvod" : proizvod, "kupljen" : True})
        elif proizvod == 'Svi proizvodi' and korisnik == 'Svi korisnici':
            oglasiResults = oglasi.find({"kupljen" : True})
        return render_template('admin_povijestProdaje.html', oglasi = oglasiResults, proizvodi = proizvodi, korisnici = korisnici, pro = proizvod, kor = korisnik)
    