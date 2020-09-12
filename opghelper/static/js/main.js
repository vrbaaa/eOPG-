var socket = io.connect('http://127.0.0.1:5000');


socket.on('connect', function() {
    socket.send(document.getElementById('imeKorisnika').innerHTML);
})



document.getElementById('sidebarCollapse').addEventListener('click', function () {
    console.log('ajoj');
    document.getElementById('sidebar').classList.toggle("active");
    if (document.getElementById('sidebar').classList.contains("active")) {
        document.getElementById('main').style.width = "100%";
    } else {
        document.getElementById('main').style.width = "90%";
    }
});
// var psad = document.getElementById('send_to_korisnicko_ime').placeholder;
// psad = encodeURIComponent(psad.trim());
// console.log(psad);
// if (window.location.pathname == '/posaljiPoruku/'+psad){
//     console.log('bome je');
// }

var private_socket = io('http://127.0.0.1:5000/private');

private_socket.on('pokazi', function(msg) {
    var citatelj = document.getElementById('imeKorisnika').innerHTML;
    posiljatelj = encodeURIComponent(citatelj.trim());
    posiljatelja = encodeURIComponent(msg['posiljatelj'].trim());
    var today = new Date();
            var dd = String(today.getDate()).padStart(2, '0');
            var mm = String(today.getMonth() + 1).padStart(2, '0');
            var yyyy = today.getFullYear();

            today = dd + '.' + mm + '.' + yyyy;
    if (window.location.pathname.includes('/posaljiPoruku/')){
        var pr = document.getElementById('send_to_korisnicko_ime').placeholder;
        if (msg['posiljatelj'] ==  pr) {
            
            var mojDiv = document.getElementById('nov');
            const h2 = document.createElement('h2');
            const h5 = document.createElement('h5');
            const p = document.createElement('p');
            const hr = document.createElement('hr');
        
            h2.textContent = msg['posiljatelj'];
            h5.textContent = 'Datum : ' + today;
            p.textContent = 'poruka: ' + msg['poruka'];
        
            mojDiv.append(h2, h5, p, hr);
        }
        if (window.location.pathname == '/posaljiPoruku/' + posiljatelja) {
            console.log("Ova poruka je sada pročitana");
            private_socket.emit('procitana', {'por_id' : msg['por_id']});
        }
    } 
        else {
            private_socket.emit('prikaziNotifikaciju', {'citatelj' : citatelj}); 
        }  

        if (window.location.pathname == '/porukee') {
            var mojDiv = document.getElementById('poruka'+ msg['posiljatelj']);
            if (!mojDiv) {
                var mojDiv = document.getElementById('container');

                const div = document.createElement('div');
                div.setAttribute('id', 'poruka'+ msg['posiljatelj']);

                const datum = document.createElement('p');
                datum.textContent = today;
                datum.setAttribute("id", 'datum'+ msg['posiljatelj']);

                const pos = document.createElement('h2');
                pos.setAttribute("id", 'posiljatelj'+ msg['posiljatelj']);
                pos.textContent = msg['posiljatelj'];

                const poo = document.createElement('p');
                poo.setAttribute("id", 'poruka'+ msg['posiljatelj']);
                poo.textContent = msg['poruka'];

                const bb = document.createElement('strong');
                bb.textContent = 'Broj nepročitanih poruka: ';
                const span = document.createElement('span');
                span.setAttribute("id", 'broj'+ msg['posiljatelj']);
                span.textContent = '1';
                bb.appendChild(span);
                div.append(datum, pos, poo, bb);
                mojDiv.appendChild(div);
            } else {
                var datum = document.getElementById('datum'+ msg['posiljatelj']);
                var poruka = document.getElementById('sadrzaj'+ msg['posiljatelj']);
                var broj = document.getElementById('broj'+ msg['posiljatelj']);
                var brojNepr = parseInt(broj.innerText, 10);
                datum.textContent = today;
                poruka.textContent = msg['poruka'];
                broj.textContent = brojNepr+1;
                if (!broj) {
                    var broj = document.createElement('strong');
                    broj.textContent = 'Broj nepročitanih poruka: ';
                    var span = document.createElement('span');
                    span.setAttribute("id", 'broj'+ msg['posiljatelj']);
                    span.textContent = '1';
                    broj.appendChild(span);
                    mojDiv.append(broj);
                }
            }
        }
});

private_socket.on('azurNotif', function(msg){
    var notif = document.getElementById('notif');
    notif.innerHTML = msg['brojNeprocitanih'];
});


document.getElementById('posalji').onclick = function() {
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var yyyy = today.getFullYear();

    today = dd + '.' + mm + '.' + yyyy;
    var pr = document.getElementById('send_to_korisnicko_ime').placeholder;
    var poruka = document.getElementById('poruka').value;
    var posiljatelj = document.getElementById('imeKorisnika').innerHTML;

    var mojDiv = document.getElementById('nov');
    var mojDrugi = document.createElement('div');
    const h2 = document.createElement('h2');
    const h5 = document.createElement('h5');
    const p = document.createElement('p');
    const hr = document.createElement('hr');

    mojDrugi.className = 'levo';
    h2.textContent = 'JA';
    h5.textContent = 'Datum : ' + today;
    p.textContent = 'poruka: '+ poruka;

    mojDrugi.append(h2, h5, p);
    mojDiv.append(mojDrugi);
    document.getElementById('poruka').value = '';
    private_socket.emit('private_message', {'korisnicko_ime' : pr, 'poruka' : poruka, 'posiljatelj' : posiljatelj});
}
if (window.location.pathname.includes('/posaljiPoruku')){
    console.log('Delam');
    var lastslashindex = window.location.pathname.lastIndexOf('/');
    var result = window.location.pathname.substring(lastslashindex  + 1);
    posiljatelj = decodeURIComponent(result);
    console.log("Poruke za korisnika " + posiljatelj);
    var primatelj = document.getElementById('imeKorisnika').innerHTML;
    console.log(result, primatelj);
    private_socket.emit('procitaj', {'posiljatelj' : posiljatelj, 'primatelj': primatelj});
}

var resize = document.querySelector("d-flex justify-content-between align-items-center");
var btni = document.querySelector("btn-group");

window.addEventListener("resize", function() {
    console.log(window.innerWidth);
    if (window.innerWidth < 1000) {
        resize.classList.remove("d-flex justify-content-between");
        btni.removeAttribute('class');
    } 
  });

  console.log(window.location);
  window.onresize = console.log(window.innerWidth);
window.onload = function() {
    var notif = document.getElementById('notif');
    // notif.textContent = msg['brojNeprocitanih'];
    console.log(notif);
}
