const SUPABASE_URL = "https://fgljrlyxylhfaeeqijyoe.supabase.co"
const SUPABASE_KEY = "SUA_ANON_PUBLIC_KEY"

const supabase = window.supabase.createClient(
  SUPABASE_URL,
  SUPABASE_KEY
)

document.getElementById("login-form").addEventListener("submit", async (e)=>{

e.preventDefault()

const email = document.getElementById("email").value
const password = document.getElementById("password").value

const { data, error } = await supabase.auth.signInWithPassword({

email: email,
password: password

})

if(error){

alert("Erro de login")

}else{

window.location.href = "index.html"

}

})
