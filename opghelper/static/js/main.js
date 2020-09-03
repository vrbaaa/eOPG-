var socket = io.connect('http://127.0.0.1:5000');



var private_socket = io('http://127.0.0.1:5000/private');
document.getElementById('posalji').onclick = function() {
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var yyyy = today.getFullYear();

    today = dd + '.' + mm + '.' + yyyy;
    var pr = document.getElementById('send_to_username').placeholder;
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
    private_socket.emit('private_message', {'username' : pr, 'poruka' : poruka, 'posiljatelj' : posiljatelj});
}

socket.on('connect', function() {
    socket.send(document.getElementById('imeKorisnika').innerHTML);
})

document.getElementById('sidebarCollapse').addEventListener('click', function () {
    document.getElementById('sidebar').classList.toggle("active");
    if (document.getElementById('sidebar').classList.contains("active")) {
        document.getElementById('main').style.width = "100%";
    } else {
        document.getElementById('main').style.width = "90%";
    }
});


private_socket.on('pokazi', function(msg) {
    var pr = document.getElementById('send_to_username').placeholder;
    if (msg['posiljatelj'] ==  pr) {
        var today = new Date();
        var dd = String(today.getDate()).padStart(2, '0');
        var mm = String(today.getMonth() + 1).padStart(2, '0');
        var yyyy = today.getFullYear();

        today = dd + '.' + mm + '.' + yyyy;
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
});

var resize = document.querySelector("d-flex justify-content-between align-items-center");
var btni = document.querySelector("btn-group");

window.addEventListener("resize", function() {
    console.log(window.innerWidth);
    if (window.innerWidth < 1000) {
        resize.classList.remove("d-flex justify-content-between");
        btni.removeAttribute('class');
    } 
  });

  console.log(window.location.href);
  window.onresize = console.log(window.innerWidth);

