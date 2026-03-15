const API = "https://cti-backend-5ugf.onrender.com"

async function carregarDados(){

try{

const equipamentos = await fetch(API + "/equipamentos").then(r=>r.json())
const implementadores = await fetch(API + "/implementadores").then(r=>r.json())
const clientes = await fetch(API + "/clientes").then(r=>r.json())
const metas = await fetch(API + "/metas").then(r=>r.json())

renderLinha(equipamentos)
renderOEM(implementadores)
renderClientes(clientes)
renderMetas(metas)

}catch(e){

console.error("Erro ao carregar dados",e)

}

}

function renderLinha(data){

const linhas = {}

data.forEach(e=>{
linhas[e.linha] = (linhas[e.linha] || 0) + 1
})

new Chart(document.getElementById("linhaChart"),{
type:"pie",
data:{
labels:Object.keys(linhas),
datasets:[{data:Object.values(linhas)}]
}
})

}

function renderOEM(data){

const contagem = {}

data.forEach(i=>{
contagem[i.nome] = (contagem[i.nome] || 0) + 1
})

new Chart(document.getElementById("oemChart"),{
type:"bar",
data:{
labels:Object.keys(contagem),
datasets:[{data:Object.values(contagem)}]
}
})

}

function renderClientes(data){

const estados = {}

data.forEach(c=>{
estados[c.estado] = (estados[c.estado]||0)+1
})

new Chart(document.getElementById("clientesChart"),{
type:"bar",
data:{
labels:Object.keys(estados),
datasets:[{data:Object.values(estados)}]
}
})

}

function renderMetas(data){

if(!data || data.length === 0){

console.warn("Nenhuma meta cadastrada")
return

}

const m = data[0]

new Chart(document.getElementById("metasChart"),{
type:"radar",
data:{
labels:["Faturamento","Novos Clientes","Reativação","Mix","Share"],
datasets:[{
data:[
m.meta_faturamento,
m.meta_novos_clientes,
m.meta_reativacao,
m.meta_mix,
m.meta_share
]
}]
}
})

}

carregarDados()
