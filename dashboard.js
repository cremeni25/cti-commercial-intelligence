const API = "https://cti-backend-5ugf.onrender.com";


async function loadDashboard() {

    window.location.hash = "dashboard";

    try {

        const response = await fetch(API + "/analytics/inteligencia-comercial");
        const data = await response.json();

        renderGraficos(data);

    } catch (error) {

        console.error("Erro ao carregar dashboard:", error);

    }

}



async function loadMarket() {

    window.location.hash = "market";

    try {

        const response = await fetch(API + "/analytics/radar-mercado");
        const data = await response.json();

        renderRadarMercado(data);

    } catch (error) {

        console.error("Erro ao carregar market intelligence:", error);

    }

}



async function loadClients() {

    window.location.hash = "clients";

    try {

        const response = await fetch(API + "/analytics/radar-clientes");
        const data = await response.json();

        renderRadarClientes(data);

    } catch (error) {

        console.error("Erro ao carregar client radar:", error);

    }

}



async function loadOEM() {

    window.location.hash = "oem";

    try {

        const response = await fetch(API + "/analytics/radar-oem");
        const data = await response.json();

        renderRadarOEM(data);

    } catch (error) {

        console.error("Erro ao carregar OEM radar:", error);

    }

}



async function loadLocadoras() {

    window.location.hash = "locadoras";

    try {

        const response = await fetch(API + "/analytics/radar-locadoras");
        const data = await response.json();

        renderRadarLocadoras(data);

    } catch (error) {

        console.error("Erro ao carregar radar locadoras:", error);

    }

}



async function loadUploads() {

    window.location.hash = "uploads";

    const content = document.getElementById("content");

    content.innerHTML = `
        <h2>Uploads de Dados</h2>

        <p>Envie arquivos ANFIR ou planilhas de mercado.</p>

        <input type="file" id="fileUpload"/>

        <button onclick="enviarArquivo()">Enviar</button>
    `;

}



async function loadAnalytics() {

    window.location.hash = "analytics";

    try {

        const response = await fetch(API + "/analytics/inteligencia-comercial");
        const data = await response.json();

        renderAnalytics(data);

    } catch (error) {

        console.error("Erro ao carregar analytics:", error);

    }

}



function renderGraficos(data) {

    console.log("Dados dashboard:", data);

}



function renderRadarMercado(data) {

    console.log("Radar mercado:", data);

}



function renderRadarClientes(data) {

    console.log("Radar clientes:", data);

}



function renderRadarOEM(data) {

    console.log("Radar OEM:", data);

}



function renderRadarLocadoras(data) {

    console.log("Radar locadoras:", data);

}



function renderAnalytics(data) {

    console.log("Analytics:", data);

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

        console.error("Erro upload:", error);

    }

}
