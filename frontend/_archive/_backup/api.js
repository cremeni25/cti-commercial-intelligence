const API_URL = "https://cti-backend-5ugf.onrender.com";

async function fetchAPI(endpoint){

const response = await fetch(API_URL + endpoint);

return response.json();

}

function loadMarket(){

document.getElementById("content").innerHTML = "<h2>Market Intelligence</h2>";

}

function loadClients(){

document.getElementById("content").innerHTML = "<h2>Client Radar</h2>";

}

function loadOEM(){

document.getElementById("content").innerHTML = "<h2>OEM Radar</h2>";

}

function loadLocadoras(){

document.getElementById("content").innerHTML = "<h2>Locadoras</h2>";

}

function loadUploads(){

document.getElementById("content").innerHTML = "<h2>Uploads</h2>";

}

function loadAnalytics(){

document.getElementById("content").innerHTML = "<h2>Analytics</h2>";

}
