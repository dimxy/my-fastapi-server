import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  type UserPublic,
  type UserRegister,
  UsersService,
} from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  console.log('isLoggedIn logged_user=', localStorage.getItem("logged_user"));
  return getUser() !== null
}

const apiBase: string = import.meta.env.VITE_API_URL || "http://localhost:8000";
const apiUrl: string = `${apiBase}/api/v1`;

const getUser = () : string | null => {
  return localStorage.getItem("logged_user")
}

const setUser = (user: string | null) => {
  if (user)
    localStorage.setItem("logged_user", user)
  else
    localStorage.removeItem("logged_user")
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  // Not used if keycloak
  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async () => {
    console.log('useAuth login entered');
    
    fetch(`${apiUrl}/users/me`, {
      credentials: "include",
      mode: "cors"
    })
    .then((res) => {
      if (res.status === 401) {
        // Yes we should navigate to the login API call. Otherwise, if we do 'fetch', we will get CORS error when connecting to keycloak.
        // In fact, this is actual for localhost connections, in prod this would not matter if connect via proxy. 
        window.location.href = `${apiUrl}/auth/login?redirect_uri=${window.location.origin}/items`;
        setUser(null);
        return null;
      }
      return res.json();
    })
    .then((resJson) => {
      if (resJson?.email) {
        console.log("Setting user:", JSON.stringify(resJson));
        setUser(resJson?.email);
        window.location.href = "/items";
      }
    })
    .catch((err) => {
      setUser(null);
      console.error(err);
    });
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
    window.location.href = `${apiUrl}/auth/logout?redirect_uri=${window.location.origin}/items`;
    setUser(null);
    /* NOTE: this does not work with keycloak due to cors issues. In fact only the navigate mode (setting window.location.href) works okay:
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
    signUpMutation,
    loginMutation,
    login,
    logout,
    user,
  }
}

export { isLoggedIn }
export default useAuth
