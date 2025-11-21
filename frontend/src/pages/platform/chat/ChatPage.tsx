import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send } from "lucide-react";

export default function ChatPage() {
  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        <div className="flex justify-start">
          <div className="bg-muted p-3 rounded-lg max-w-[80%]">
            Hello! How can I help you today?
          </div>
        </div>
        <div className="flex justify-end">
          <div className="bg-primary text-primary-foreground p-3 rounded-lg max-w-[80%]">
            I need help building a new agent.
          </div>
        </div>
      </div>
      <div className="p-4 border-t flex gap-2">
        <Input placeholder="Type your message..." />
        <Button size="icon">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
