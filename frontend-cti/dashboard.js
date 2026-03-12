// CTI - Dashboard Controller

const API_BASE = "https://cti-backend-5ugf.onrender.com";

async function carregarDashboard() {

    try {

        const resposta = await fetch(`${API_BASE}/analytics/inteligencia-comercial`);
        const dados = await resposta.json();

        renderResumo(dados.resumo_geral);
        renderLinhas(dados.performance_por_linha);
        renderEstados(dados.performance_por_estado);
        renderOEM(dados.ranking_oem);
        renderOportunidades(dados.oportunidades_detectadas);

    } catch (erro) {

        console.error("Erro ao carregar dashboard:", erro);

    }

}

function renderResumo(resumo) {

    document.getElementById("total-vendas").innerText = resumo.total_vendas;
    document.getElementById("faturamento-total").innerText =
        "R$ " + resumo.faturamento_total.toLocaleString("pt-BR");

}

function renderLinhas(linhas) {

    const container = document.getElementById("linhas");

    container.innerHTML = "";

    linhas.forEach(linha => {

        const item = document.createElement("div");
        item.className = "card";

        item.innerHTML = `
            <h3>Linha ${linha.linha}</h3>
            <p>Vendas: ${linha.vendas}</p>
            <p>Faturamento: R$ ${linha.faturamento.toLocaleString("pt-BR")}</p>
        `;

        container.appendChild(item);

    });

}

function renderEstados(estados) {

    const container = document.getElementById("estados");

    container.innerHTML = "";

    estados.forEach(estado => {

        const item = document.createElement("div");
        item.className = "card";

        item.innerHTML = `
            <h3>${estado.estado}</h3>
            <p>Vendas: ${estado.vendas}</p>
            <p>Faturamento: R$ ${estado.faturamento.toLocaleString("pt-BR")}</p>
        `;

        container.appendChild(item);

    });

}

function renderOEM(oems) {

    const container = document.getElementById("oem");

    container.innerHTML = "";

    oems.forEach(oem => {

        const item = document.createElement("div");
        item.className = "card";

        item.innerHTML = `
            <h3>${oem.oem}</h3>
            <p>Vendas: ${oem.vendas}</p>
            <p>Faturamento: R$ ${oem.faturamento.toLocaleString("pt-BR")}</p>
        `;

        container.appendChild(item);

    });

}

function renderOportunidades(lista) {

    const container = document.getElementById("oportunidades");

    container.innerHTML = "";

    lista.forEach(o => {

        const item = document.createElement("div");
        item.className = "alert";

        item.innerHTML = `
            <strong>${o.tipo}</strong><br>
            ${o.observacao}
        `;

        container.appendChild(item);

    });

}

carregarDashboard();

// ===============================
// CTI GRÁFICOS
// ===============================

async function carregarGraficosCTI() {

    const resposta = await fetch("https://cti-backend-5ugf.onrender.com/analytics/inteligencia-comercial");
    const dados = await resposta.json();

    const linhas = dados.performance_por_linha;
    const estados = dados.performance_por_estado;
    const oems = dados.ranking_oem;

    const ctxLinhas = document.getElementById("grafico-linhas");

    new Chart(ctxLinhas, {
        type: "bar",
        data: {
            labels: linhas.map(l => l.linha),
            datasets: [{
                label: "Vendas por Linha",
                data: linhas.map(l => l.vendas)
            }]
        }
    });

    const ctxEstados = document.getElementById("grafico-estados");

    new Chart(ctxEstados, {
        type: "bar",
        data: {
            labels: estados.map(e => e.estado),
            datasets: [{
                label: "Vendas por Estado",
                data: estados.map(e => e.vendas)
            }]
        }
    });

    const ctxOEM = document.getElementById("grafico-oem");

    new Chart(ctxOEM, {
        type: "pie",
        data: {
            labels: oems.map(o => o.oem),
            datasets: [{
                label: "Ranking OEM",
                data: oems.map(o => o.vendas)
            }]
        }
    });

}

window.addEventListener("load", carregarGraficosCTI);

// =============================
// CTI DASHBOARD ENGINE
// =============================

const API = "https://cti-backend-5ugf.onrender.com";

// =============================
// DASHBOARD PRINCIPAL
// =============================

async function loadDashboard() {

    try {

        const response = await fetch(API + "/analytics/inteligencia-comercial");
        const data = await response.json();

        renderGraficos(data);

    } catch (error) {

        console.error("Erro ao carregar dashboard:", error);

    }

}

// =============================
// RENDERIZAÇÃO DOS GRÁFICOS
// =============================

function renderGraficos(data) {

    const linhas = data.performance_por_linha;
    const estados = data.performance_por_estado;
    const oems = data.ranking_oem;

    renderGraficoLinhas(linhas);
    renderGraficoEstados(estados);
    renderGraficoOEM(oems);

}

// =============================
// GRÁFICO LINHAS
// =============================

function renderGraficoLinhas(linhas) {

    const ctx = document.getElementById("grafico-linhas");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: linhas.map(l => l.linha),
            datasets: [{
                label: "Vendas por Linha",
                data: linhas.map(l => l.vendas)
            }]
        }
    });

}

// =============================
// GRÁFICO ESTADOS
// =============================

function renderGraficoEstados(estados) {

    const ctx = document.getElementById("grafico-estados");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: estados.map(e => e.estado),
            datasets: [{
                label: "Vendas por Estado",
                data: estados.map(e => e.vendas)
            }]
        }
    });

}

// =============================
// GRÁFICO OEM
// =============================

function renderGraficoOEM(oems) {

    const ctx = document.getElementById("grafico-oem");

    new Chart(ctx, {
        type: "pie",
        data: {
            labels: oems.map(o => o.oem),
            datasets: [{
                label: "Ranking OEM",
                data: oems.map(o => o.vendas)
            }]
        }
    });

}

// =============================
// AUTO LOAD
// =============================

window.addEventListener("load", loadDashboard);
