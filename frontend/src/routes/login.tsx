import {
  createFileRoute,
  redirect,
} from "@tanstack/react-router"

import useAuth, { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Log In - FastAPI Cloud",
      },
    ],
  }),
})

function Login() {
  console.log('Login entered')
  const { login } = useAuth()
  login()
}
