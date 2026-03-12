function loadDashboard() {

document.getElementById("content").innerHTML = `
<h2>Dashboard</h2>

<p>Carregando dados do mercado...</p>

<div id="dashboard-data"></div>

`;

fetchAPI("/status").then(data => {

document.getElementById("dashboard-data").innerHTML = `

<p>API Status: ${data.status}</p>

`;

});

}
