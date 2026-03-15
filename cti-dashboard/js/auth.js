const SUPABASE_URL = "https://fgljrlyxylhfaeeqijyoe.supabase.co"
const SUPABASE_KEY = "SUA_ANON_KEY"

const supabase = window.supabase.createClient(
  SUPABASE_URL,
  SUPABASE_KEY
)

document.getElementById("login-form").addEventListener("submit", async (e) => {

  e.preventDefault()

  const email = document.getElementById("email").value
  const password = document.getElementById("password").value

  const { data, error } = await supabase.auth.signInWithPassword({

    email,
    password

  })

  if (error) {

    alert("Erro de login")

  } else {

    localStorage.setItem("cti_token", data.session.access_token)

    window.location.href = "dashboard.html"

  }

})
