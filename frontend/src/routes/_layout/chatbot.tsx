import { createFileRoute } from "@tanstack/react-router"
import { useRef, useState } from "react"
import { LlmsService } from "@/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/_layout/chatbot")({
  component: Chatbot,
  head: () => ({
    meta: [
      {
        title: "Chatbot - FastAPI Cloud",
      },
    ],
  }),
})

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}

function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000"

  const addMessage = (text: string, isUser: boolean) => {
    const message: Message = {
      id: Date.now().toString(),
      text,
      isUser,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, message])
  }

  const handleSendText = async () => {
    if (!inputText.trim()) return

    const userMessage = inputText.trim()
    setInputText("")
    addMessage(userMessage, true)
    setIsLoading(true)

    try {
      const response = await LlmsService.processChat({
        requestBody: { message: userMessage },
      })
      addMessage(response.response, false)
    } catch (error) {
      console.error("Error processing chat:", error)
      addMessage("Sorry, there was an error processing your message.", false)
    } finally {
      setIsLoading(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/wav",
        })
        await sendVoice(audioBlob)
        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error("Error starting recording:", error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const sendVoice = async (audioBlob: Blob) => {
    setIsLoading(true)
    addMessage("Processing voice...", true)

    try {
      const formData = new FormData()
      formData.append("audio", audioBlob, "recording.wav")

      const response = await fetch(`${apiBase}/api/v1/llms/parse_voice`, {
        method: "POST",
        body: formData,
        credentials: "include",
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const audioResponseBlob = await response.blob()
      const audioUrl = URL.createObjectURL(audioResponseBlob)

      // Play the audio response
      if (audioRef.current) {
        audioRef.current.src = audioUrl
        audioRef.current.play()
      }

      addMessage("Voice response played", false)
    } catch (error) {
      console.error("Error processing voice:", error)
      addMessage("Sorry, there was an error processing your voice.", false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendText()
    }
  }

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle>Chatbot</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Chat Messages */}
            <div className="h-96 overflow-y-auto border rounded p-4 space-y-2">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`p-2 rounded ${
                    message.isUser
                      ? "bg-blue-100 ml-auto max-w-xs"
                      : "bg-gray-100 mr-auto max-w-xs"
                  }`}
                >
                  <p>{message.text}</p>
                  <small className="text-gray-500">
                    {message.timestamp.toLocaleTimeString()}
                  </small>
                </div>
              ))}
              {isLoading && (
                <div className="bg-gray-100 mr-auto max-w-xs p-2 rounded">
                  <p>Thinking...</p>
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="flex space-x-2">
              <Input
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button
                onClick={handleSendText}
                disabled={isLoading || !inputText.trim()}
              >
                Send
              </Button>
              <Button
                onClick={isRecording ? stopRecording : startRecording}
                variant={isRecording ? "destructive" : "secondary"}
                disabled={isLoading}
              >
                {isRecording ? "Stop Recording" : "Record Voice"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Hidden audio element for playing responses */}
      <audio ref={audioRef} />
    </div>
  )
}
