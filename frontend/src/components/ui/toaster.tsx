import { useToast } from "@/hooks/use-toast"
import { Toast } from "@/components/ui/toast"

export function Toaster() {
  const { toasts, dismiss } = useToast()

  return (
    <>
      {toasts.map(function ({ id, title, description, variant, ...props }) {
        const message = description ? `${title} - ${description}` : title
        const type = variant === "destructive" ? "error" : "info"
        
        return (
          <Toast
            key={id}
            message={message as string}
            type={type}
            onClose={() => dismiss(id)}
            {...props}
          />
        )
      })}
    </>
  )
}
