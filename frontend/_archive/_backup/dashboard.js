const API = "https://cti-backend-5ugf.onrender.com";

// ---------------------
// DASHBOARD
// ---------------------

async function loadDashboard(){

    window.location.hash="dashboard";

    const content=document.getElementById("content");

    content.innerHTML="<p>Carregando dashboard...</p>";

    try{

        const response=await fetch(API+"/analytics/inteligencia-comercial");
        const data=await response.json();

        renderDashboard(data);

    }catch(error){

        content.innerHTML="<p>Erro ao carregar dados</p>";

    }

}

function renderDashboard(data){

    const total=data?.resumo_geral?.total_vendas??0;
    const faturamento=data?.resumo_geral?.faturamento_total??0;

    const estados=data.performance_por_estado||[];
    const linhas=data.performance_por_linha||[];
    const oems=data.ranking_oem||[];

    const content=document.getElementById("content");

    content.innerHTML=`

    <h2>Dashboard Comercial</h2>

    <!-- BLOCO DE INTELIGÊNCIA -->
    <div class="grid">

        <div class="card alert">
            <h3>⚠️ Alertas</h3>
            <ul id="alertas"></ul>
        </div>

        <div class="card oportunidade">
            <h3>🚀 Oportunidades</h3>
            <ul id="oportunidades"></ul>
        </div>

        <div class="card diagnostico">
            <h3>🧠 Diagnóstico</h3>
            <ul id="diagnostico"></ul>
        </div>

    </div>

    <br>

    <!-- KPIs -->
    <div class="cards">

        <div class="card">
            <h3>Total de Vendas</h3>
            <p>${total}</p>
        </div>

        <div class="card">
            <h3>Faturamento</h3>
            <p>R$ ${faturamento}</p>
        </div>

    </div>

    <br>

    <!-- GRÁFICOS -->
    <div class="charts">

        <canvas id="graficoEstados"></canvas>
        <canvas id="graficoLinhas"></canvas>
        <canvas id="graficoOEM"></canvas>

    </div>

    `;

    // gráficos continuam iguais
    renderGraficoEstados(estados);
    renderGraficoLinhas(linhas);
    renderGraficoOEM(oems);

    // 🔥 NOVO: inteligência
    carregarInteligencia();
}

// ---------------------
// INTELIGÊNCIA
// ---------------------

async function carregarInteligencia(){

    try{

        const res = await fetch(API + "/inteligencia/decisoes");
        const data = await res.json();

        document.getElementById("alertas").innerHTML =
            (data.alertas || []).map(a => `<li>${a}</li>`).join("");

        document.getElementById("oportunidades").innerHTML =
            (data.oportunidades || []).map(o => `<li>${o}</li>`).join("");

        document.getElementById("diagnostico").innerHTML =
            (data.diagnostico || []).map(d => `<li>${d}</li>`).join("");

    }catch(e){

        console.error("Erro inteligência", e);

    }
}

// ---------------------
// GRÁFICOS
// ---------------------

function renderGraficoEstados(estados){

    const labels=estados.map(e=>e.estado);
    const valores=estados.map(e=>e.vendas);

    new Chart(document.getElementById("graficoEstados"),{

        type:"bar",

        data:{
            labels:labels,
            datasets:[{
                label:"Vendas por Estado",
                data:valores
            }]
        }

    });

}

function renderGraficoLinhas(linhas){

    const labels=linhas.map(e=>e.linha);
    const valores=linhas.map(e=>e.vendas);

    new Chart(document.getElementById("graficoLinhas"),{

        type:"pie",

        data:{
            labels:labels,
            datasets:[{
                data:valores
            }]
        }

    });

}

function renderGraficoOEM(oems){

    const labels=oems.map(e=>e.oem);
    const valores=oems.map(e=>e.vendas);

    new Chart(document.getElementById("graficoOEM"),{

        type:"doughnut",

        data:{
            labels:labels,
            datasets:[{
                data:valores
            }]
        }

    });

}

// ---------------------
// UPLOAD
// ---------------------

function loadUploads(){

    window.location.hash="uploads";

    const content=document.getElementById("content");

    content.innerHTML=`

    <h2>Upload ANFIR</h2>

    <input type="file" id="uploadAnfir">

    <br><br>

    <button id="btnUpload">Enviar</button>

    <p id="statusUpload"></p>

    `;

    document.getElementById("btnUpload").addEventListener("click",enviarANFIR);

}

async function enviarANFIR(){

    const input=document.getElementById("uploadAnfir");
    const status=document.getElementById("statusUpload");

    if(!input.files.length){
        alert("Selecione um arquivo");
        return;
    }

    const file=input.files[0];

    const formData=new FormData();
    formData.append("file",file);

    status.innerHTML="Enviando arquivo...";

    try{

        const response=await fetch(API+"/upload/anfir",{
            method:"POST",
            body:formData
        });

        const data=await response.json();

        status.innerHTML="Upload concluído";

        console.log(data);

    }catch(error){

        status.innerHTML="Erro no upload";

        console.error(error);

    }

}

// ---------------------
// OUTROS MENUS
// ---------------------

function loadMarket(){
    document.getElementById("content").innerHTML="<h2>Market Intelligence</h2>";
}

function loadClients(){
    document.getElementById("content").innerHTML="<h2>Client Radar</h2>";
}

function loadOEM(){
    document.getElementById("content").innerHTML="<h2>OEM Radar</h2>";
}

function loadLocadoras(){
    document.getElementById("content").innerHTML="<h2>Locadoras</h2>";
}

function loadAnalytics(){
    document.getElementById("content").innerHTML="<h2>Analytics</h2>";
}
