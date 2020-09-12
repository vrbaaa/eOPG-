from flask import render_template, url_for, flash, redirect, request, session, jsonify, Blueprint
from opghelper import app, mongo, bcrypt
from flask_login import login_user, current_user, logout_user
from bson.objectid import ObjectId
from datetime import datetime
import smtplib
import json
import requests
from opghelper.opg.forms import OglasForm, OcjenaForm, MessageForm


users = mongo.db.korisnici
products = mongo.db.proizvodi
offers = mongo.db.offers
protuponude = mongo.db.protuponude
protuponudeZaCentar = mongo.db.protuponudeZaCentar
oglasi = mongo.db.oglasi
poruke = mongo.db.poruke

opg = Blueprint('opg', __name__)

dnevnik = mongo.db.dnevnik
def upisiUDnevnik(radnja):
    if (session['type'] != 'admin'):
        dnevnik.insert_one(
                            {
                                "korisnik" : session['korisnicko_ime'],
                                "radnja" : radnja,
                                "vrijeme" : datetime.now()
                            }
                        )
    
@opg.route('/predajaOglasa', methods=['GET', 'POST'])
def predajaOglasa():
    if (session['type'] == 'opg'):
        form = OglasForm()
        kor = []
        form.proizvod.choices = [(proizvod['naziv'], proizvod['naziv']) for proizvod in products.find({})]
        print(form.errors)
        if form.validate_on_submit():
            upisiUDnevnik("Dodavanje novog oglasa")
            oglasi.insert_one({
                "objavio" : session['korisnicko_ime'],
                "naziv" : form.naziv.data,
                "cijena" : form.cijena.data,
                "kolicina" :form.kolicina.data,
                "prijevoz" : form.prijevoz.data,
                "proizvod" : form.proizvod.data,
                "datumDostave" : datetime.strptime(str(form.datumDostave.data), '%Y-%m-%d'),
                "datumIVrijemeObjavljivanja" : datetime.now(),
                "kupljen" : False,
                "zatvoren" : False,
                "tipObjavio" : session['type']
            })
            flash('Objavili ste uspješno novi oglas!', 'success')
            ogl = oglasi.distinct("objavio", {"kupljen" : False, "tipObjavio" : "centar", "proizvod" : form.proizvod.data, "kolicina" : {"$gte" : form.kolicina.data}})
            for og in ogl:
                us = list(users.find({"korisnicko_ime" : og}))
                message = "OPG " + session['korisnicko_ime'] + "je objavio oglas za proizvod " + form.proizvod.data +" Kolicina : " + str(form.proizvod.data) +" Cijena " + str(form.cijena.data) +" kn. Posaljite mu poruku preko sustava i dogovorite kupnju proizvoda."
                msg = message.encode('utf-8')
                server  = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login("opg.aplikacija@gmail.com", "ZavrsniRadFoi2020")
                server.sendmail("opg.aplikacija@gmail.com", us[0]['email'], msg)
            return redirect(url_for('opg.mojiOglasi'))
        else:
            print(form.errors)
        return render_template('forma-centar.html', form=form)

@opg.route('/izbrisiOglas/<string:oglas_id>',  methods=['GET'])
def izbrisiOglas(oglas_id):
    if (session['type'] == 'opg' or session['type'] == 'admin'):
        oglasi.delete_one({"_id" : ObjectId(oglas_id)})
        upisiUDnevnik("Brisanje oglasa")
        flash('Izbrisali ste oglas!', 'success')
        if (session['type'] == 'admin'):
            return redirect(url_for('admin.aktivniOglasi')) 
        else: 
            return redirect(url_for('opg.mojiOglasi'))
    

@opg.route('/mojiOglasi' )
def mojiOglasi():
    if (session['type'] == 'opg'):
        productsResults = list(products.find({}))
        offersResults = list(oglasi.find({"objavio" : session['korisnicko_ime'], "kupljen" : False}))
        usersResults = users.find({})
        print(session['type'])
        return render_template("mog.html", oglasi = offersResults, users = usersResults, products = productsResults)

@opg.route('/azurirajOglas/<string:oglas_id>', methods=['GET', 'POST'])
def azurirajOglas(oglas_id):
    if (session['type'] == 'opg' or session['type'] == 'admin'):
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
                                "datumDostave" : datetime.strptime(str(request.form.get('datumDostave')), '%d.%m.%Y.'),
                            }
                            })
            flash('Uspješno ste ažurirali oglas!', 'success')
        if (session['type'] == 'admin'):
            return redirect(url_for('admin.aktivniOglasi'))
        else:
            return redirect(url_for('opg.mojiOglasi'))

@opg.route('/povijestProdaje')
def povijestProdaje():
    if (session['type'] == 'opg'):
        offersResults = oglasi.find({"kupljen" : True, "prodavatelj" : session['korisnicko_ime']})
        return render_template("povijestProdaje.html", oglasi = offersResults)
    if (session['type'] == 'admin'):
        return redirect(url_for('admin.aktivniOglasi'))

@opg.route('/prihvatiOglasCentra/<string:oglas_id>', methods=['GET'])
def prihvatiOglasCentra(oglas_id):
    if (session['type'] == 'opg'):
        oglas = list(oglasi.find({"_id" : ObjectId(oglas_id)}))
        email = list(users.find({"korisnicko_ime" : oglas[0]['objavio']}))
        message = "Centar prihvatio je vas oglas za proizvod " + oglas[0]['proizvod'] +" Kolicina : " + str(oglas[0]['kolicina']) +" Cijena " + str(oglas[0]['cijena']) +" kn. Posaljite mu poruku preko sustava kako biste dogovorili detalje."
        server  = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("opg.aplikacija@gmail.com", "ZavrsniRadFoi2020")
        server.sendmail("opg.aplikacija@gmail.com", email[0]['email'], message)
        upisiUDnevnik("Prihvaćanje oglasa")
        oglasi.update_one({"_id" : ObjectId(oglas_id)}, 
                            {"$set" :
                            {
                                "datumKupnje" : datetime.now(),
                                "kupljen" : True,
                                "prodavatelj" : session['korisnicko_ime'],
                                "kupac_id" : oglas[0]['objavio']
                            }
                            })
        if (session['type'] == 'admin'):
            return redirect(url_for('admin.aktivniOglasi'))
        else: 
            return redirect(url_for('opg.povijestProdaje'))

@opg.route('/posaljiProtuponuduCentru/<string:oglas_id>', methods=['GET', 'POST'])
def posaljiProtuponuduCentru(oglas_id):
    if (session['type'] == 'opg'):
        if request.method == 'POST': 
            upisiUDnevnik("Slanje protuponude")
            mongo.db.protuponudeZaCentar.insert_one({
                "oglas_id" : oglas_id,
                "cijena" : float(request.form.get('cijena')),
                "kolicina" : float(request.form.get('kolicina')),
                "prijevoz" : request.form.get('prijevoz'),
                "user_id" : session['korisnicko_ime'],
                "odbijena" : False,
                "prihvacena" : False
            })
            return redirect(url_for('users.index'))
    
@opg.route('/prikaziProtuponude/<string:oglas_id>')
def prikaziProtuponude(oglas_id): 
        offerResult = oglasi.find_one({"_id" : ObjectId(oglas_id)})
        protuponudeResults = protuponude.find({"oglas_id" : oglas_id, "odbijena" : False, "prihvacena" : False})
        return render_template('protuponude.html', offer = offerResult, protuponude = protuponudeResults)


@opg.route('/prihvatiProtuponudu/<string:protuponuda_id>', methods=['GET', 'POST'])
def prihvatiProtuponudu(protuponuda_id): 
        protuponudaZaUpdate = list(protuponude.find({"_id" : ObjectId(protuponuda_id)}))
        oglasZaUpdate = list(oglasi.find({"_id" : ObjectId(protuponudaZaUpdate[0]['oglas_id'])}))
        novaKolicina = float(oglasZaUpdate[0]['kolicina']) - float(protuponudaZaUpdate[0]['kolicina'])
        upisiUDnevnik("Prihvaćanje protuponude")
        if novaKolicina <= 0:
            oglasi.update_one(
                {"_id" : ObjectId(protuponudaZaUpdate[0]['oglas_id'])},
                {"$set" :
                    {   "cijena" : float(protuponudaZaUpdate[0]['cijena']),
                        "kolicina" : float(protuponudaZaUpdate[0]['kolicina']),
                        "zatvoren" : True,
                        "kupljen" : True,
                        "kupac_id" : protuponudaZaUpdate[0]['user_id'],
                        "datumKupnje" : datetime.now()
                    }
                })
            protuponude.update({"oglas_id": protuponudaZaUpdate[0]['oglas_id']},
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
                "prodavatelj" : oglasZaUpdate[0]['objavio'],
                "kupac_id" : protuponudaZaUpdate[0]['user_id'],
                "kupljen" :  True,
                "datumDostave" : oglasZaUpdate[0]['datumDostave'],
                "datumKupnje" : datetime.now()
            })
        protuponude.update_one({"_id" : ObjectId(protuponuda_id)}, 
                            {"$set" :
                            {
                                "prihvacena" : True
                            }
                            })
        
        return redirect(url_for('opg.povijestProdaje'))

@opg.route('/odbijProtuponudu/<string:protuponuda_id>', methods=['GET', 'POST'])
def odbijProtuponudu(protuponuda_id): 
        upisiUDnevnik("Odbijanje protuponude")
        protuponude.update_one({"_id" : ObjectId(protuponuda_id)}, 
                            {"$set" :
                            {
                                "odbijena" : True
                            }
                            })
        flash('Odbili ste ponudu!', 'warning')
        return redirect(url_for('opg.mojiOglasi'))

@opg.route('/pretragaOglasa')
def pretragaOglasa():
    if (session['type'] == 'opg'):
        prot = []
        oglasResults = list(oglasi.find({"kupljen" : False,  "tipObjavio" : "centar"}).sort("datumDostave", 1))
        proizvod = 'Svi proizvodi'
        cijena = None
        productResults = products.find({})
        usersResults = users.find({})
        proizvod = request.get_data().decode('UTF-8')
        protuponudeZaCentarRes = list(protuponudeZaCentar.find({"user_id" : session['korisnicko_ime'], "odbijena" : False, "prihvacena" : False}, {"oglas_id":1, "_id":0}))
        for pr in protuponudeZaCentarRes:
            ogid = pr['oglas_id']
            ogid.replace("'","")
            prot.append(ogid)
        return render_template("pretragaOglasa.html", oglasi = oglasResults, users = usersResults, products = productResults, prot = prot)

@opg.route('/opg.search')
def search():
    if (session['type'] == 'opg'):
        productResults = products.find({})
        proizvod = request.args.get('proizvod')
        if (request.args.get('cijena') != ''):
            cijena = float(request.args.get('cijena'))
        else:
            cijena = None
        if proizvod != 'Svi proizvodi' and not cijena:  
            offersResults = oglasi.find({"kupljen" : False, "proizvod" : proizvod, "tipObjavio" : "centar"})
        elif proizvod != 'Svi proizvodi' and cijena:
            offersResults = oglasi.find({"kupljen" : False, "tipObjavio" : "centar", "proizvod" : proizvod, "cijena" : {"$lte" : cijena}})
        elif proizvod == 'Svi proizvodi' and not cijena:
            offersResults = oglasi.find({"kupljen" : False, "tipObjavio" : "centar"})
        elif proizvod == 'Svi proizvodi' and cijena:
            offersResults = oglasi.find({"kupljen" : False, "tipObjavio" : "centar", "cijena" : {"$lte" : cijena}})
        return render_template("pretragaOglasa.html", oglasi = offersResults, products = productResults, proizvod = proizvod, cijena = cijena)
    
@opg.route('/pregledCentara')
def pregledCentara():
    if (session['type'] == 'opg'):
        centri = list(users.find({"type": "centar"}))
        
        ocjene = {}
        ocjena = []
        for centar in centri:
            ocjene['id'] = centar['_id']
            ocjene['korisnicko_ime'] = centar['korisnicko_ime']
            ukupnaOcjena = 0
            ocjene['avg'] = 0
            brojac = 0
            brojOcjena = len(centar['ocjene'])
            kors = []
            for x in centar['ocjene']:
                if x != '': 
                    brojac = brojac + 1
                    ukupnaOcjena += x['rating']
                    ocjene['avg'] = ukupnaOcjena / brojac
                    kors.append(x['user_id'])
                else:
                    ocjene['avg'] = 'Nema ocjena za centar'
            ukPos = oglasi.find({"kupljen" : True, "kupac_id" : centar['korisnicko_ime'], "prodavatelj": session['korisnicko_ime']}).count()
            ocjene['brojPoslova'] = ukPos
            ocjene['kors'] = kors
            ocjena.append(dict(ocjene))
        print(ocjena)
        return render_template('pregledCentara.html', centri = centri, ja = session['korisnicko_ime'], ocjene = ocjena)

@opg.route('/ocjeniCentar/<string:centar_id>', methods=['GET', 'POST'])
def ocjeniCentar(centar_id):
    if (session['type'] == 'opg'):
        user = list(users.find({"_id" : ObjectId(centar_id)}))
        if int(request.form.get('ocjena')) > 5 or int(request.form.get('ocjena')) < 1:
            flash('Ne smijete ocjeniti korisnika s tom ocjenom')
        else:
            users.update_one({"korisnicko_ime": user[0]['korisnicko_ime']},
                                {"$push": 
                                    {"ocjene" : 
                                        {"user_id" : session['korisnicko_ime'], "rating": int(request.form.get('ocjena'))}}})
        return redirect(url_for('opg.pregledCentara'))

@opg.route('/novaPoruka', methods=['GET', 'POST'])
def novaPoruka():
    form = MessageForm()
    print(form.errors)
    if form.validate_on_submit():
        print('OOOOOOOOOOOO')
        print(form.primatelj.data)        
        return redirect(url_for('users.index'))
    print(form.errors)
    return render_template("novaPoruka.html", form = form)

@opg.route('/posaljiPoruku/<string:centar>', methods=['GET', 'POST'])
def posaljiPoruku(centar):
    form = MessageForm()
    c = centar
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
                         {"primatelj" : centar},
                         {"posiljatelj" : centar}
                       ]
               }
             ]
    })
    return render_template("novaPoruka.html", form = form, centar = c, poruke = por)