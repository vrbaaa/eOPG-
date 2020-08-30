from flask import render_template, url_for, flash, redirect, request, session, jsonify, Blueprint
from opghelper import app, mongo, bcrypt, io
from flask_login import login_user, current_user, logout_user
from bson.objectid import ObjectId
from datetime import datetime
import smtplib
from opghelper.centri.forms import OglasForm, MessageForm
from flask_socketio import SocketIO, send, emit


import json
import requests

users = mongo.db.users
products = mongo.db.products
offers = mongo.db.offers
protuponude = mongo.db.protuponude
poruke = mongo.db.poruke
protuponudeZaCentar = mongo.db.protuponudeZaCentar
oglasi = mongo.db.oglasi
dnevnik = mongo.db.dnevnik
def upisiUDnevnik(radnja):
    if (session['type'] != 'admin'):
        dnevnik.insert_one(
                            {
                                "korisnik" : session['username'],
                                "radnja" : radnja,
                                "vrijeme" : datetime.now()
                            }
                        )
centri = Blueprint('centri', __name__)

korisnici = {}
mice = {}

@centri.route('/oglasiOpgova',  methods=['GET', 'POST'])
def oglasiOpgova():
    # if (session['type'] == 'centar'):
        proizvod = 'Svi proizvodi'
        cijena = None
        productResults = products.find({})
        proizvod = request.get_data().decode('UTF-8')
        offersResults = oglasi.find({"kupljen" : False, "tipObjavio" : "opg"})
        return render_template("oglasiOpgova.html", offers = offersResults, products = productResults, proizvod = proizvod, cijena = cijena)
    
    
@centri.route('/search')
def search():
    if (session['type'] == 'centar'):
        productResults = products.find({})
        proizvod = request.args.get('proizvod')
        if (request.args.get('cijena') != ''):
            cijena = float(request.args.get('cijena'))
        else:
            cijena = None
        if proizvod != 'Svi proizvodi' and not cijena:  
            offersResults = oglasi.find({"kupljen" : False, "proizvod" : proizvod, "tipObjavio" : "opg"})
        elif proizvod != 'Svi proizvodi' and cijena:
            offersResults = oglasi.find({"kupljen" : False, "tipObjavio" : "opg", "proizvod" : proizvod, "cijena" : {"$lte" : cijena}})
        elif proizvod == 'Svi proizvodi' and not cijena:
            offersResults = oglasi.find({"kupljen" : False, "tipObjavio" : "opg"})
        elif proizvod == 'Svi proizvodi' and cijena:
            offersResults = oglasi.find({"kupljen" : False, "tipObjavio" : "opg", "cijena" : {"$lte" : cijena}})
        return render_template("oglasiOpgova.html", offers = offersResults, products = productResults, proizvod = proizvod, cijena = cijena)

@centri.route('/prihvatiOglas/<string:oglas_id>', methods=['GET'])
def prihvatiOglas(oglas_id):
    if (session['type'] == 'centar'):
        upisiUDnevnik("Prihvaćanje oglasa")
        oglas = list(oglasi.find({"_id" : ObjectId(oglas_id)}))
        email = list(users.find({"username" : oglas[0]['objavio']}))
        message = f"Centar " + session['username'] + " prihvatio je vas oglas " + oglas[0]['naziv'] + " za proizvod " + oglas[0]['proizvod'] +" Kolicina : " + str(oglas[0]['kolicina']) +" Cijena " + str(oglas[0]['cijena']) +" kn. Posaljite mu poruku preko sustava kako biste dogovorili detalje."
        server  = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("opg.aplikacija@gmail.com", "ZavrsniRadFoi2020")
        server.sendmail("opg.aplikacija@gmail.com", email[0]['email'], message)
        oglasi.update_one({"_id" : ObjectId(oglas_id)}, 
                            {"$set" :
                            {
                                "datumKupnje" : datetime.now(),
                                "kupljen" : True,
                                "kupac_id" : session['username']
                            }
                            })
        return redirect(url_for('centri.povijestKupnje'))



@centri.route('/povijestKupnje')
def povijestKupnje():
    if (session['type'] == 'centar'):
        oglasResults = oglasi.find({"kupljen" : True, "kupac_id" : session['username']})
        return render_template("povijestKupnje.html", oglasi = oglasResults)
    
@centri.route('/posaljiProtuponudu/<string:oglas_id>', methods=['GET', 'POST'])
def posaljiProtuponudu(oglas_id):
    if (session['type'] == 'centar'):
        if request.method == 'POST': 
            upisiUDnevnik("Slanje protuponude")
            mongo.db.protuponude.insert_one({
                "oglas_id" : oglas_id,
                "cijena" : float(request.form.get('wantedPrice')),
                "kolicina" : float(request.form.get('quantity')),
                "prijevoz" : request.form.get('transport'),
                "user_id" : session['username'],
                "odbijena" : False,
                "prihvacena" : False
            })
            return redirect(url_for('centri.oglasiOpgova'))
        
@centri.route('/prikaziProtuponudeCentar/<string:oglas_id>')
def prikaziProtuponudeCentar(oglas_id):
    if (session['type'] == 'centar'): 
        offerResult = oglasi.find_one_or_404({"_id" : ObjectId(oglas_id)})
        protuponudeResults = protuponudeZaCentar.find({"oglas_id" : oglas_id, "odbijena" : False, "prihvacena" : False})
        return render_template('protuponudeCentar.html', offer = offerResult, protuponude = protuponudeResults)

@centri.route('/odbijProtuponuduCentar/<string:protuponuda_id>')
def odbijProtuponuduCentar(protuponuda_id): 
    if (session['type'] == 'centar'):
        upisiUDnevnik("Odbijanje protuponude")
        protuponudeZaCentar.update_one({"_id" : ObjectId(protuponuda_id)}, 
                            {"$set" :
                            {
                                "odbijena" : True
                            }
                            })
        flash('Uspješno ste ažurirali oglas!', 'success')
        return redirect(url_for('centri.mojiOglasiCentar'))

@centri.route('/prihvatiProtuponuduCentar/<string:protuponudaZaCentar_id>', methods=['GET', 'POST'])
def prihvatiProtuponuduCentar(protuponudaZaCentar_id): 
    if (session['type'] == 'centar'):
        upisiUDnevnik("Prihvaćanje protuponude")
        protuponudaZaUpdate = list(protuponudeZaCentar.find({"_id" : ObjectId(protuponudaZaCentar_id)}))
        oglasZaUpdate = list(oglasi.find({"_id" : ObjectId(protuponudaZaUpdate[0]['oglas_id'])}))
        novaKolicina = float(oglasZaUpdate[0]['kolicina']) - float(protuponudaZaUpdate[0]['kolicina'])
        if novaKolicina <= 0:
            oglasi.update_one(
                {"_id" : ObjectId(protuponudaZaUpdate[0]['oglas_id'])},
                {"$set" :
                    {   "cijena" : float(protuponudaZaUpdate[0]['cijena']),
                        "kolicina" : float(protuponudaZaUpdate[0]['kolicina']),
                        "zatvoren" : True,
                        "kupljen" : True,
                        "kupac_id" : session['username'],
                        "prodavatelj" : protuponudaZaUpdate[0]['user_id'],
                        "datumKupnje" : datetime.now()
                    }
                })
            protuponudeZaCentar.update({"oglas_id": protuponudaZaUpdate[0]['oglas_id']},
                {"$set" : 
                    {
                        "odbijena" : True
                    }
                    })
        else: 
            oglasi.update_one(
                {"_id" : ObjectId(protuponudaZaUpdate[0]['oglas_id'])},
                {"$set" :
                    { "kolicina" : novaKolicina }
                })
            oglasi.insert_one({
                "naziv" : oglasZaUpdate[0]['naziv'],
                "cijena" : float(protuponudaZaUpdate[0]['cijena']),
                "kolicina" : float(protuponudaZaUpdate[0]['kolicina']),
                "proizvod" : oglasZaUpdate[0]['proizvod'],
                "prijevoz" : protuponudaZaUpdate[0]['prijevoz'],
                "kupac_id" : session['username'],
                "prodavatelj" : protuponudaZaUpdate[0]['user_id'],
                "zatvoren" : True,
                "kupljen" :  True,
                "datumKupnje" : datetime.now()
            })
        protuponudeZaCentar.update_one({"_id" : ObjectId(protuponudaZaCentar_id)}, 
                            {"$set" :
                            {
                                "prihvacena" : True
                            }
                            })
        return redirect(url_for('centri.mojiOglasiCentar'))

@centri.route('/dodajOglasCentar', methods=['GET', 'POST'])
def dodajOglasCentar():
    if (session['type'] == 'centar'):
        upisiUDnevnik("Dodavanje novog oglasa")
        form = OglasForm()
        form.proizvod.choices = [(proizvod['name'], proizvod['name']) for proizvod in products.find({})]
        print(form.errors)
        if form.validate_on_submit():
            oglasi.insert_one({
                "objavio" : session['username'],
                "naziv" : form.naziv.data,
                "cijena" : form.cijena.data,
                "kolicina" : form.kolicina.data,
                "prijevoz" : form.prijevoz.data,
                "proizvod" : form.proizvod.data,
                "datumDostave" : datetime.strptime(str(form.datumDostave.data), '%Y-%m-%d'),
                "datumIVrijemeObjavljivanja" : datetime.now(),
                "zatvoren" : False,
                "kupljen" : False,
                "tipObjavio" : session['type']
            })
            flash('Objavili ste uspješno novi oglas!', 'success')
            ogl = oglasi.distinct("objavio", {"kupljen" : False, "tipObjavio" : "opg", "proizvod" : form.proizvod.data, "kolicina" : {"$lte" : form.kolicina.data}})
            for og in ogl:
                us = list(users.find({"username" : og}))
                message = "Centar " + session['username'] + "je objavio oglas za proizvod " + form.proizvod.data +" Kolicina : " + str(form.proizvod.data) +" Cijena " + str(form.cijena.data) +" kn. Posaljite mu poruku preko sustava i dogovorite kupnju proizvoda."
                msg = message.encode('utf-8')
                server  = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login("opg.aplikacija@gmail.com", "ZavrsniRadFoi2020")
                server.sendmail("opg.aplikacija@gmail.com", us[0]['email'], msg)
            return redirect(url_for('centri.mojiOglasiCentar'))
        else:
            print(form.errors)
        return render_template('forma-centar.html', form=form)
    
@centri.route('/obrisiOglas/<string:oglas_id>',  methods=['GET'])
def obrisiOglas(oglas_id):
    if (session['type'] == 'centar'):
        upisiUDnevnik("Brisanje oglasa")
        oglasi.delete_one({"_id" : ObjectId(oglas_id)})
        flash('Izbrisali ste oglas!', 'success')
        return redirect(url_for('centri.mojiOglasiCentar'))
    
@centri.route('/mojiOglasiCentar')
def mojiOglasiCentar():
    if (session['type'] == 'centar'):
        oglasResults = list(oglasi.find({"objavio" : session['username'], "kupljen" : False}))
        productsResults = list(products.find({}))
        usersResults = users.find({})
        
        return render_template("mojiOglasi-centar.html", oglasi = oglasResults, users = usersResults, products = productsResults)

@centri.route('/azurirajOglasCentar/<string:oglas_id>', methods=['GET', 'POST'])
def azurirajOglasCentar(oglas_id):
    if (session['type'] == 'centar'):
        if request.method == 'POST': 
            upisiUDnevnik("Ažuriranje oglasa")
            oglasi.update_one({"_id" : ObjectId(oglas_id)}, 
                            {"$set" :
                            {
                                "naziv" : request.form.get('naziv'),
                                "cijena" : float(request.form.get('cijena')),
                                "kolicina" : float(request.form.get('kolicina')),
                                "prijevoz" : request.form.get('prijevoz'),
                                "proizvod" : request.form.get('proizvod'),
                                "datumKupnje" : datetime.strptime(str(request.form.get('datumKupnje')), '%d.%m.%Y.'),
                            }
                            })
            flash('Uspješno ste ažurirali oglas!', 'success')
            return redirect(url_for('centri.mojiOglasiCentar'))
    
@centri.route('/profilCentar')
def profilCentar():
    if (session['type'] == 'centar'):
        res = users.find_one({"username": session['username']})
        uk = len(res['ratings'])
        ukupnaOcjena = 0
        for x in res['ratings']:
            ukupnaOcjena += x['rating']
        prosjek = ukupnaOcjena / uk
        kupnja = oglasi.find({"centar_id" : session['username']})
        for x in kupnja:
            print(x)
        return render_template("profilCentar.html", user = res, prosjek = prosjek)

@centri.route('/pregledOpgova')
def pregledOpgova():
    if (session['type'] == 'centar'):
        centri = list(users.find({"type": "opg"}))
        ocjene = {}
        ocjena = []
        try: 
            for centar in centri:
                useri = []
                ocjene['id'] = centar['_id']
                ocjene['username'] = centar['username']
                ukupnaOcjena = 0
                ocjene['avg'] = 0
                brojac = 0
                brojOcjena = len(centar['ratings'])
                for x in centar['ratings']:
                    if x != '': 
                        brojac = brojac + 1
                        ukupnaOcjena += x['rating']
                        ocjene['avg'] = ukupnaOcjena / brojac
                        useri.append(x['user_id'])
                    else:
                        ocjene['avg'] = 'Nema ocjena za opg'
                ukPos = oglasi.find({"kupljen" : True, "prodavatelj" : centar['username'], "kupac_id": session['username']}).count()
                ocjene['brojPoslova'] = ukPos
                ocjene['useri'] = useri
                ocjena.append(dict(ocjene))
        except Exception as ex: 
            print(ex)
        print(ocjena)
        return render_template('pregledOpgova.html', centri = centri, ja = session['username'], ocjene = ocjena)

@centri.route('/ocijeniOpg/<string:opg_id>', methods=['GET', 'POST'])
def ocijeniOpg(opg_id):
        user = list(users.find({"_id" : ObjectId(opg_id)}))
        if int(request.form.get('ocjena')) > 5 or int(request.form.get('ocjena')) < 1:
            flash('Ne smijete ocjeniti korisnika s tom ocjenom')
        else:
            users.update_one({"username": user[0]['username']},
                                {"$push": 
                                    {"ratings" : 
                                        {"user_id" : session['username'], "rating": int(request.form.get('ocjena'))}}})
        if (session['type'] == 'centar'):
            return redirect(url_for('centri.pregledOpgova'))
        if (session['type'] == 'admin'):
            return redirect(url_for('admin.admin_popis_korisnika'))


@io.on('message')
def handleMessage(msg):
    korisnici[msg] = request.sid
    print(korisnici)
    print('Message: ' + msg)


@io.on('private_message', namespace='/private')
def private_message(input):
    if input['username'] in korisnici:
        try:
            primatelj_session_id = korisnici[input['username']]
        except Exception as inst: 
            print(type(inst))
            print(inst.args)
            print(inst)
        poruka = input['poruka']
        # upisiUDnevnik("Slanje poruke")
        poruke.insert_one({"posiljatelj" : input['posiljatelj'], "primatelj" : input['username'], "poruka" : input['poruka'], "datum_slanja" : datetime.now()})
        emit('pokazi', {'poruka' : poruka, 'posiljatelj' : input['posiljatelj']}, room=primatelj_session_id)
    else: 
        poruke.insert_one({"posiljatelj" : input['posiljatelj'], "primatelj" : input['username'], "poruka" : input['poruka'], "datum_slanja" : datetime.now()})

    
@centri.route('/posaljiPoruku/<string:opg>', methods=['GET', 'POST'])
def posaljiPoruku(opg):
    form = MessageForm()
    c = opg
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
                         {"primatelj" : opg},
                         {"posiljatelj" : opg}
                       ]
               }
             ]
    })
    return render_template("novaPoruka.html", form = form, centar = c, poruke = por)

    