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
