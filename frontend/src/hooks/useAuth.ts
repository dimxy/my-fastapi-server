import { useMutation, useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import { type UserPublicKC, UsersService } from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  console.log("isLoggedIn logged_user=", localStorage.getItem("logged_user"))
  return getUser() !== null
}

const apiBase: string = import.meta.env.VITE_API_URL || "http://localhost:8000"
const apiUrl: string = `${apiBase}/api/v1`

const homePage: string = "/generate-video"

const getUser = (): string | null => {
  return localStorage.getItem("logged_user")
}

const setUser = (user: string | null) => {
  if (user) localStorage.setItem("logged_user", user)
  else localStorage.removeItem("logged_user")
}

const useAuth = () => {
  const navigate = useNavigate()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery<UserPublicKC | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  const login = async () => {
    console.log("useAuth login entered")

    fetch(`${apiUrl}/users/me`, {
      credentials: "include",
      mode: "cors",
    })
      .then((res) => {
        if (res.status === 401) {
          // Yes we should navigate to the login API call. Otherwise, if we do 'fetch', we will get CORS error when connecting to keycloak.
          // In fact, this is actual for localhost connections, in prod this would not matter if connecting via proxy.
          window.location.href = `${apiUrl}/auth/login?redirect_uri=${window.location.origin}{homePage}`
          setUser(null)
          return null
        }
        return res.json()
      })
      .then((resJson) => {
        if (resJson?.email) {
          console.log("Setting user:", JSON.stringify(resJson))
          setUser(resJson?.email)
          window.location.href = homePage
        }
      })
      .catch((err) => {
        setUser(null)
        console.error(err)
      })
  }

  // Not used if keycloak
  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = () => {
    window.location.href = `${apiUrl}/auth/logout?redirect_uri=${window.location.origin}{homePage}`
    setUser(null)
    /* NOTE: fetch does not work with keycloak due to its CORS issues (apparently this is for purpose). 
    If both keycloak and api server not behind proxy, we should use the navigate mode (setting window.location.href):
    fetch(`${apiUrl}/auth/logout?redirect_uri=${window.location.origin}/`, {
      credentials: "include",
      redirect: "follow",
      mode: "cors"
    })
    .finally(() => {
      setUser(null);
      window.location.href = "/";
    }); */
  }

  return {
    // signUpMutation,
    loginMutation,
    login,
    logout,
    user,
  }
}

export { isLoggedIn }
export default useAuth
