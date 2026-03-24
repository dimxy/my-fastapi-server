import { useState } from "react"
import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/generate-video")({
  component: GenerateVideo,
  head: () => ({
    meta: [
      {
        title: "Generate Video - FastAPI Cloud",
      },
    ],
  }),
})

function GenerateVideo() {
  const [prompt, setPrompt] = useState("")
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000"

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setStatusMessage(null)
    setVideoUrl(null)

    if (!prompt.trim()) {
      setStatusMessage("Please enter a prompt")
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(
        `${apiBase}/api/v1/llms/generate_video?prompt=${encodeURIComponent(prompt.trim())}`,
        {
          method: "GET",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        },
      )

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`API error ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      if (!data?.file_path) {
        throw new Error("No video URL returned from backend")
      }

      setVideoUrl(`${apiBase}/${data.file_path}`)
      setStatusMessage("Video generated successfully")
    } catch (error) {
      console.error(error)
      setStatusMessage(error instanceof Error ? error.message : "Failed to generate video")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Generate Video</h1>
        <p className="text-muted-foreground">
          Enter a prompt and click Generate to call backend /generate_video.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block text-sm font-medium text-muted-foreground" htmlFor="prompt">
          Prompt
        </label>
        <input
          id="prompt"
          name="prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="A short video of a sunrise over mountains"
          className="w-full rounded border p-2 text-base"
        />

        <button
          type="submit"
          className="inline-flex items-center rounded bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary/80 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={isLoading}
        >
          {isLoading ? "Generating..." : "Generate video"}
        </button>
      </form>

      {statusMessage ? (
        <p className="text-sm text-muted-foreground">{statusMessage}</p>
      ) : null}

      {videoUrl ? (
        <div className="space-y-2">
          <p className="text-sm font-medium">Generated video output</p>
          <video
            controls
            src={videoUrl}
            className="w-full max-h-120 rounded border"
            onError={() => setStatusMessage("Could not load generated video")}
          />
        </div>
      ) : null}
    </div>
  )
}
