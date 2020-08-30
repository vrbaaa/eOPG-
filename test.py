from opghelper import app
from flask import url_for
import unittest
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

class FlaskTestCase(unittest.TestCase):
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        
    def test_login_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertTrue(b'Lozinka' in response.data)
        
    #provjeri login s pravim vrijednostima
    def test_login_prave_vrijednosti(self):
        tester = app.test_client()
        response = tester.post(
            '/',
            data=dict(username='admin', password='administrator'),
            follow_redirects=True
        )
        self.assertIn(b'Prijavljeni ste', response.data)
    #provjeri login s krivim vrijednostima
    def test_login_krive_vrijednosti(self):
        tester = app.test_client()
        response = tester.post(
            '/',
            data=dict(username="wrong", password="wrong"),
            follow_redirects=True
        )
        self.assertIn(b'ime ili lozinka', response.data)
    
    #provjeri logout
    def test_logout(self):
        tester = app.test_client()
        tester.post(
            '/',
            data={'username':'admin', 'password':'administrator'},
            follow_redirects=True
        )
        response = tester.get('/logout', follow_redirects=True)
        self.assertIn(b'Odjava', response.data)
    
    def test_main_route_requires_login(self):
        tester = app.test_client()
        response = tester.get('/admin_popis_korisnika', follow_redirects=True)
        self.assertIn(b'Morate se prijaviti', response.data)

    def test_pretraga(self):
        tester = app.test_client(self)
        tester.post(
            '/',
            data={'username':'admin', 'password':'administrator'},
            follow_redirects=True
        )
        response = tester.get('/admin_popis_korisnika', follow_redirects=True)
        self.assertIn(b'Tip', response.data)
    
        
    def test_oglasiopg(self):
        tester = app.test_client()
        response = tester.get('/oglasiOpgova', follow_redirects=True)
        self.assertIn(b'Proizvodu', response.data)
        
    def test_ucitavanje_apija(self):
        tester = app.test_client()
        response = tester.get('/opcina/KOPRIVNIČKO-KRIŽEVAČKA')
        self.assertIn(b'Virje', response.data)
        

        
if __name__ == '__main__':
    unittest.main()
