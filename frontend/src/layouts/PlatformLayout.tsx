import { Link, Outlet, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Toaster } from "@/components/ui/toaster";
import { 
  LayoutDashboard, 
  Bot, 
  MessageSquare, 
  Bug, 
  Settings,
  LogOut,
  Users,
  Workflow,
  Boxes
} from "lucide-react";

export default function PlatformLayout() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-muted/30 flex flex-col">
        <div className="p-6 border-b">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Bot className="h-6 w-6" />
            AI Platform
          </h1>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          <Link to="/platform/dashboard">
            <Button 
              variant={isActive("/platform/dashboard") ? "secondary" : "ghost"} 
              className="w-full justify-start gap-2"
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </Button>
          </Link>
          <Link to="/platform/agents">
            <Button 
              variant={isActive("/platform/agents") ? "secondary" : "ghost"} 
              className="w-full justify-start gap-2"
            >
              <Boxes className="h-4 w-4" />
              Agentes
            </Button>
          </Link>
          <Link to="/platform/workflows">
            <Button 
              variant={isActive("/platform/workflows") || isActive("/platform/studio") ? "secondary" : "ghost"} 
              className="w-full justify-start gap-2"
            >
              <Workflow className="h-4 w-4" />
              Workflows
            </Button>
          </Link>
          <Link to="/platform/chat">
            <Button 
              variant={isActive("/platform/chat") ? "secondary" : "ghost"} 
              className="w-full justify-start gap-2"
            >
              <MessageSquare className="h-4 w-4" />
              Chat
            </Button>
          </Link>
          
          <div className="pt-4 mt-4 border-t">
            <p className="px-4 text-xs font-medium text-muted-foreground mb-2">Admin</p>
            <Link to="/platform/users">
              <Button 
                variant={isActive("/platform/users") ? "secondary" : "ghost"} 
                className="w-full justify-start gap-2"
              >
                <Users className="h-4 w-4" />
                Users
              </Button>
            </Link>
          </div>

          <div className="pt-4 mt-4 border-t">
            <p className="px-4 text-xs font-medium text-muted-foreground mb-2">Developer</p>
            <Link to="/platform/debug">
              <Button 
                variant={isActive("/platform/debug") ? "secondary" : "ghost"} 
                className="w-full justify-start gap-2"
              >
                <Bug className="h-4 w-4" />
                Debug Console
              </Button>
            </Link>
          </div>
        </nav>

        <div className="p-4 border-t space-y-2">
          <Button variant="ghost" className="w-full justify-start gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </Button>
          <Link to="/">
            <Button variant="ghost" className="w-full justify-start gap-2 text-red-500 hover:text-red-600 hover:bg-red-50">
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
      <Toaster />
    </div>
  );
}
