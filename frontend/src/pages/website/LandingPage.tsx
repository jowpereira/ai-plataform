import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b p-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">AI Platform</h1>
        <nav className="flex gap-4">
          <Link to="/login">
            <Button variant="outline">Login</Button>
          </Link>
        </nav>
      </header>
      <main className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <h2 className="text-4xl font-bold mb-4">Build and Deploy AI Agents</h2>
        <p className="text-xl text-muted-foreground mb-8">
          The complete platform for orchestrating generative AI workflows.
        </p>
        <div className="flex gap-4">
          <Link to="/platform/dashboard">
            <Button size="lg">Get Started</Button>
          </Link>
          <Link to="/platform/debug">
            <Button variant="secondary" size="lg">Debug Mode</Button>
          </Link>
        </div>
      </main>
    </div>
  );
}
