import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate, redirect } from "@tanstack/react-router"

import {
  type Body_login_login_access_token as AccessToken,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  //console.log('isLoggedIn=', localStorage.getItem("access_token") !== null);
  console.log('isLoggedIn logged_user=', localStorage.getItem("logged_user"));
  return getUser() !== null
}

const apiHost: string = "http://localhost:8000/api/v1";

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

  const login0 = async (data: AccessToken) => {
    const apiHost: string = "http://localhost:8000/api/v1";
    const uri = `${apiHost}/auth/login?redirect_uri=${window.location.origin}/items&username=${data.username}&password=${data.password}`;
    window.location.href=uri;
    //const response = await LoginService.loginAccessToken({
    //  formData: data,
    //})
    const access_token = localStorage.getItem("auth-example");
    if (access_token) {
      console.log('setting access_token', access_token);
      localStorage.setItem("access_token", access_token)
    } else {
      console.log('access_token empty');
    }
  }

  const login = async (data: AccessToken) => {
    console.log('useAuth login entered');
    
    fetch(`${apiHost}/users/me`, {
      credentials: "include",
      mode: "cors"
    })
    .then((res) => {
      if (res.status === 401) {
        // Yes we should navigate to the login API call. Otherwise, if we do fetch, we will get CORS error when connecting to keycloak.
        // In fact, this is actual for localhost connections, in prod this would not matter if connect via proxy. 
        window.location.href = `${apiHost}/auth/login?redirect_uri=${window.location.origin}/items`;
        setUser(null);
        return null;
      }
      return res.json();
    })
    .then((resJson) => {
      //if (isUserDTO(resJson)) {
      if (resJson?.email) {
        console.log("Setting user:", JSON.stringify(resJson));
        setUser(resJson?.email);
        window.location.href = "/items";
      }
      //localStorage.setItem("logged_user", resJson?.email)
      //}
    })
    .catch((err) => {
      setUser(null);
      console.error(err);
    });

    /*if (getUser() !== null) {
      console.log('useAuth redirecting to items');
      redirect({ to: "/items" });
    }*/
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = () => {
    window.location.href = `${apiHost}/auth/logout?redirect_uri=${window.location.origin}/items`;
    setUser(null);
    /*fetch(`${apiHost}/auth/logout?redirect_uri=${window.location.origin}/`, {
      credentials: "include",
      redirect: "follow",
      mode: "cors"
    })
    .finally(() => {
      setUser(null);
      window.location.href = "/";
    });*/
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
