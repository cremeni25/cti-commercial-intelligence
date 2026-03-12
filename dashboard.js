const API = "https://cti-backend-5ugf.onrender.com";

async function loadDashboard() {

    window.location.hash = "dashboard";

    try {

        const response = await fetch(API + "/analytics/inteligencia-comercial");
        const data = await response.json();

        renderDashboard(data);

    } catch (error) {

        console.error("Erro ao carregar dashboard:", error);

    }

}



function renderDashboard(data) {

    const content = document.getElementById("content");

    content.innerHTML = `
        <h2>Dashboard Comercial</h2>

        <div class="dashboard-grid">

            <div class="card">
                <h3>Total de Vendas</h3>
                <p>${data.resumo_geral.total_vendas}</p>
            </div>

            <div class="card">
                <h3>Faturamento</h3>
                <p>R$ ${data.resumo_geral.faturamento_total}</p>
            </div>

        </div>

        <canvas id="graficoEstados"></canvas>
        <canvas id="graficoLinhas"></canvas>
        <canvas id="graficoOEM"></canvas>
    `;


    renderGraficoEstados(data.performance_por_estado);
    renderGraficoLinhas(data.performance_por_linha);
    renderGraficoOEM(data.ranking_oem);

}



function renderGraficoEstados(estados) {

    const labels = estados.map(e => e.estado);
    const valores = estados.map(e => e.vendas);

    new Chart(document.getElementById("graficoEstados"), {

        type: "bar",

        data: {
            labels: labels,
            datasets: [{
                label: "Vendas por Estado",
                data: valores
            }]
        }

    });

}



function renderGraficoLinhas(linhas) {

    const labels = linhas.map(l => l.linha);
    const valores = linhas.map(l => l.vendas);

    new Chart(document.getElementById("graficoLinhas"), {

        type: "pie",

        data: {
            labels: labels,
            datasets: [{
                label: "Vendas por Linha",
                data: valores
            }]
        }

    });

}



function renderGraficoOEM(oems) {

    const labels = oems.map(o => o.oem);
    const valores = oems.map(o => o.vendas);

    new Chart(document.getElementById("graficoOEM"), {

        type: "doughnut",

        data: {
            labels: labels,
            datasets: [{
                label: "Ranking OEM",
                data: valores
            }]
        }

    });

}



async function loadMarket() {

    window.location.hash = "market";

    const content = document.getElementById("content");

    content.innerHTML = "<h2>Market Intelligence</h2><p>Módulo em construção.</p>";

}



async function loadClients() {

    window.location.hash = "clients";

    const content = document.getElementById("content");

    content.innerHTML = "<h2>Client Radar</h2><p>Módulo em construção.</p>";

}



async function loadOEM() {

    window.location.hash = "oem";

    const content = document.getElementById("content");

    content.innerHTML = "<h2>OEM Radar</h2><p>Módulo em construção.</p>";

}



async function loadLocadoras() {

    window.location.hash = "locadoras";

    const content = document.getElementById("content");

    content.innerHTML = "<h2>Radar Locadoras</h2><p>Módulo em construção.</p>";

}



async function loadUploads() {

    window.location.hash = "uploads";

    const content = document.getElementById("content");

    content.innerHTML = `
        <h2>Upload ANFIR</h2>
        <input type="file" id="fileUpload"/>
        <button onclick="enviarArquivo()">Enviar</button>
    `;

}



async function loadAnalytics() {

    window.location.hash = "analytics";

    const content = document.getElementById("content");

    content.innerHTML = "<h2>Analytics</h2><p>Módulo em construção.</p>";

}



async function enviarArquivo() {

    const fileInput = document.getElementById("fileUpload");

    const file = fileInput.files[0];

    if (!file) {

        alert("Selecione um arquivo");
        return;

    }

    const formData = new FormData();
    formData.append("file", file);

    try {

        const response = await fetch(API + "/upload/anfir", {

            method: "POST",
            body: formData

        });

        const result = await response.json();

        alert("Upload concluído");

        console.log(result);

    } catch (error) {

        console.error("Erro no upload:", error);

    }

}
