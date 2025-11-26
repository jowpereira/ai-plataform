import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { Shield, Brain, Heart, ArrowRight, CheckCircle2, FileDiff, Database, Scale, Headphones, Mail, Search, GitMerge, Users, ListStart, ArrowRightLeft, MessageSquare } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground overflow-x-hidden">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-border/40">
        <div className="container mx-auto px-4 h-16 flex justify-between items-center">
          <div className="flex items-center gap-2">
            {/* MAIA Logo */}
            <svg
              width="32"
              height="32"
              viewBox="0 0 805 805"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="flex-shrink-0"
            >
              <path
                d="M402.488 119.713C439.197 119.713 468.955 149.472 468.955 186.18C468.955 192.086 471.708 197.849 476.915 200.635L546.702 237.977C555.862 242.879 566.95 240.96 576.092 236.023C585.476 230.955 596.218 228.078 607.632 228.078C644.341 228.078 674.098 257.836 674.099 294.545C674.099 316.95 663.013 336.765 646.028 348.806C637.861 354.595 631.412 363.24 631.412 373.251V430.818C631.412 440.83 637.861 449.475 646.028 455.264C663.013 467.305 674.099 487.121 674.099 509.526C674.099 546.235 644.341 575.994 607.632 575.994C598.598 575.994 589.985 574.191 582.133 570.926C573.644 567.397 563.91 566.393 555.804 570.731L469.581 616.867C469.193 617.074 468.955 617.479 468.955 617.919C468.955 654.628 439.197 684.386 402.488 684.386C365.779 684.386 336.021 654.628 336.021 617.919C336.021 616.802 335.423 615.765 334.439 615.238L249.895 570C241.61 565.567 231.646 566.713 223.034 570.472C214.898 574.024 205.914 575.994 196.47 575.994C159.761 575.994 130.002 546.235 130.002 509.526C130.002 486.66 141.549 466.49 159.13 454.531C167.604 448.766 174.349 439.975 174.349 429.726V372.538C174.349 362.289 167.604 353.498 159.13 347.734C141.549 335.774 130.002 315.604 130.002 292.738C130.002 256.029 159.761 226.271 196.47 226.271C208.223 226.271 219.263 229.322 228.843 234.674C238.065 239.827 249.351 241.894 258.666 236.91L328.655 199.459C333.448 196.895 336.021 191.616 336.021 186.18C336.021 149.471 365.779 119.713 402.488 119.713ZM475.716 394.444C471.337 396.787 468.955 401.586 468.955 406.552C468.955 429.68 457.142 450.048 439.221 461.954C430.571 467.7 423.653 476.574 423.653 486.959V537.511C423.653 547.896 430.746 556.851 439.379 562.622C449 569.053 461.434 572.052 471.637 566.592L527.264 536.826C536.887 531.677 541.164 520.44 541.164 509.526C541.164 485.968 553.42 465.272 571.904 453.468C580.846 447.757 588.054 438.749 588.054 428.139V371.427C588.054 363.494 582.671 356.676 575.716 352.862C569.342 349.366 561.663 348.454 555.253 351.884L475.716 394.444ZM247.992 349.841C241.997 346.633 234.806 347.465 228.873 350.785C222.524 354.337 217.706 360.639 217.706 367.915V429.162C217.706 439.537 224.611 448.404 233.248 454.152C251.144 466.062 262.937 486.417 262.937 509.526C262.937 519.654 267.026 529.991 275.955 534.769L334.852 566.284C344.582 571.49 356.362 568.81 365.528 562.667C373.735 557.166 380.296 548.643 380.296 538.764V486.305C380.296 476.067 373.564 467.282 365.103 461.516C347.548 449.552 336.021 429.398 336.021 406.552C336.021 400.967 333.389 395.536 328.465 392.902L247.992 349.841ZM270.019 280.008C265.421 282.469 262.936 287.522 262.937 292.738C262.937 293.308 262.929 293.876 262.915 294.443C262.615 306.354 266.961 318.871 277.466 324.492L334.017 354.751C344.13 360.163 356.442 357.269 366.027 350.969C376.495 344.088 389.024 340.085 402.488 340.085C416.203 340.085 428.947 344.239 439.532 351.357C449.163 357.834 461.63 360.861 471.864 355.385L526.625 326.083C537.106 320.474 541.458 307.999 541.182 296.115C541.17 295.593 541.164 295.069 541.164 294.545C541.164 288.551 538.376 282.696 533.091 279.868L463.562 242.664C454.384 237.753 443.274 239.688 434.123 244.65C424.716 249.75 413.941 252.647 402.488 252.647C390.83 252.647 379.873 249.646 370.348 244.373C361.148 239.281 349.917 237.256 340.646 242.217L270.019 280.008Z"
                fill="url(#paint0_landing)"
              />
              <defs>
                <linearGradient
                  id="paint0_landing"
                  x1="255.628"
                  y1="-34.3245"
                  x2="618.483"
                  y2="632.032"
                  gradientUnits="userSpaceOnUse"
                >
                  <stop stopColor="#E6331A" />
                  <stop offset="1" stopColor="#003366" />
                </linearGradient>
              </defs>
            </svg>
            <span className="text-xl font-bold tracking-tight text-primary">MAIA</span>
          </div>
          <nav className="flex gap-4 items-center">
            <Link to="/login">
              <Button variant="ghost" className="font-medium">Login</Button>
            </Link>
            <Link to="/platform/dashboard">
              <Button className="bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/20">
                Acessar Plataforma
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-primary/5 rounded-full blur-3xl opacity-50" />
          <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-accent/5 rounded-full blur-3xl opacity-30" />
        </div>

        <div className="container mx-auto px-4 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 text-accent text-sm font-medium mb-6 border border-accent/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
            </span>
            Mapfre Inteligência Artificial
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-primary via-primary/90 to-accent">
            MAIA
          </h1>
          
          <p className="text-2xl md:text-4xl font-medium text-foreground/80 mb-8 max-w-3xl mx-auto leading-tight">
            Inteligência que antecipa. <br className="hidden md:block" />
            <span className="text-primary">Proteção que evolui.</span>
          </p>
          
          <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto">
            A plataforma oficial para colaboradores criarem, testarem e publicarem agentes de IA 
            que transformam o dia a dia da Mapfre.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link to="/platform/dashboard">
              <Button size="lg" className="h-12 px-8 text-lg rounded-full bg-primary hover:bg-primary/90 text-white shadow-xl shadow-primary/20 transition-all hover:scale-105">
                Começar a Criar <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" size="lg" className="h-12 px-8 text-lg rounded-full border-primary/20 hover:bg-primary/5">
                Fazer Login
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Nossos Valores</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              A MAIA foi construída sobre pilares fundamentais que garantem uma tecnologia 
              humana, segura e eficiente.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Card 1 */}
            <div className="bg-card p-8 rounded-2xl border border-border/50 shadow-sm hover:shadow-md transition-all hover:-translate-y-1 group">
              <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-bold mb-3">Confiável</h3>
              <p className="text-muted-foreground">
                Segurança e robustez em cada interação. A base sólida da Mapfre aplicada 
                à tecnologia de ponta.
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-card p-8 rounded-2xl border border-border/50 shadow-sm hover:shadow-md transition-all hover:-translate-y-1 group">
              <div className="h-12 w-12 rounded-xl bg-accent/10 flex items-center justify-center mb-6 group-hover:bg-accent/20 transition-colors">
                <Brain className="h-6 w-6 text-accent" />
              </div>
              <h3 className="text-xl font-bold mb-3">Inovador</h3>
              <p className="text-muted-foreground">
                Antecipando o futuro com soluções criativas e eficientes que transformam 
                dados em insights acionáveis.
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-card p-8 rounded-2xl border border-border/50 shadow-sm hover:shadow-md transition-all hover:-translate-y-1 group">
              <div className="h-12 w-12 rounded-xl bg-destructive/10 flex items-center justify-center mb-6 group-hover:bg-destructive/20 transition-colors">
                <Heart className="h-6 w-6 text-destructive" />
              </div>
              <h3 className="text-xl font-bold mb-3">Empático</h3>
              <p className="text-muted-foreground">
                Tecnologia centrada no humano. Uma IA que entende, cuida e evolui junto 
                com as necessidades das pessoas.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Feature 1: Agent Studio */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center gap-12">
            <div className="flex-1 space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold">
                Agent Studio: <span className="text-primary">Sua Fábrica de Inteligência</span>
              </h2>
              <p className="text-lg text-muted-foreground">
                Um ambiente intuitivo onde colaboradores podem configurar prompts, definir ferramentas 
                e escolher modelos de IA sem escrever uma linha de código.
              </p>
              
              <ul className="space-y-4">
                {[
                  "Interface visual para definição de persona e instruções",
                  "Biblioteca de ferramentas seguras da Mapfre",
                  "Teste em tempo real com feedback imediato",
                  "Controle total sobre criatividade e temperatura"
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 text-accent flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              
              <div className="pt-4">
                <Link to="/platform/studio">
                  <Button variant="outline" className="gap-2">
                    Explorar o Studio <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </div>
            
            <div className="flex-1 relative">
              <div className="absolute inset-0 bg-gradient-to-tr from-primary/20 to-accent/20 rounded-2xl blur-2xl -z-10" />
              <div className="bg-card border border-border rounded-2xl shadow-2xl overflow-hidden">
                <div className="bg-muted/50 p-3 border-b flex gap-2">
                  <div className="h-3 w-3 rounded-full bg-red-500/50" />
                  <div className="h-3 w-3 rounded-full bg-yellow-500/50" />
                  <div className="h-3 w-3 rounded-full bg-green-500/50" />
                </div>
                <div className="p-6 space-y-6">
                  {/* Mock Studio UI */}
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="h-4 w-24 bg-muted rounded"></div>
                      <div className="h-10 w-full bg-background border rounded-md p-2 flex items-center text-sm">
                        Analista de Sinistros Sênior
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="h-4 w-32 bg-muted rounded"></div>
                      <div className="h-32 w-full bg-background border rounded-md p-3 text-sm text-muted-foreground font-mono">
                        Você é um especialista em análise de sinistros automotivos. 
                        Sua função é validar documentos, identificar danos em imagens 
                        e sugerir aprovações baseadas nas regras da apólice...
                      </div>
                    </div>

                    <div className="flex gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="h-4 w-20 bg-muted rounded"></div>
                        <div className="h-10 bg-background border rounded-md flex items-center px-3 text-xs gap-2">
                          <div className="h-2 w-2 rounded-full bg-green-500"></div>
                          GPT-4 Turbo
                        </div>
                      </div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 w-20 bg-muted rounded"></div>
                        <div className="h-10 bg-background border rounded-md flex items-center px-3 text-xs">
                          Temperatura: 0.3
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex justify-end pt-2">
                    <Button size="sm" className="bg-primary text-white">Salvar Agente</Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature 2: Workflow Builder */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row-reverse items-center gap-12">
            <div className="flex-1 space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold">
                Workflow Builder: <span className="text-accent">Poder de Orquestração</span>
              </h2>
              <p className="text-lg text-muted-foreground">
                A plataforma suporta nativamente os padrões de arquitetura de agentes mais 
                avançados do mercado, prontos para uso.
              </p>
              
              <div className="space-y-4 mt-4">
                <div className="flex gap-4 items-start p-3 rounded-lg hover:bg-background/50 transition-colors border border-transparent hover:border-border/50">
                  <div className="mt-1 bg-primary/10 p-2 rounded-md">
                    <ListStart className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-bold text-foreground">Sequencial</h4>
                    <p className="text-sm text-muted-foreground">
                      Execução linear e determinística. Ideal para processos com etapas 
                      bem definidas, como "Pesquisar &rarr; Resumir &rarr; Traduzir".
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 items-start p-3 rounded-lg hover:bg-background/50 transition-colors border border-transparent hover:border-border/50">
                  <div className="mt-1 bg-accent/10 p-2 rounded-md">
                    <GitMerge className="h-5 w-5 text-accent" />
                  </div>
                  <div>
                    <h4 className="font-bold text-foreground">Roteamento (Router)</h4>
                    <p className="text-sm text-muted-foreground">
                      Classificação inteligente de intenção. Um agente "porteiro" analisa 
                      o pedido e direciona para o especialista correto (ex: Sinistro vs. Vendas).
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 items-start p-3 rounded-lg hover:bg-background/50 transition-colors border border-transparent hover:border-border/50">
                  <div className="mt-1 bg-orange-500/10 p-2 rounded-md">
                    <Users className="h-5 w-5 text-orange-500" />
                  </div>
                  <div>
                    <h4 className="font-bold text-foreground">Group Chat</h4>
                    <p className="text-sm text-muted-foreground">
                      Colaboração dinâmica. Múltiplos agentes (ex: Escritor, Revisor, 
                      Pesquisador) conversam entre si para resolver problemas complexos.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 items-start p-3 rounded-lg hover:bg-background/50 transition-colors border border-transparent hover:border-border/50">
                  <div className="mt-1 bg-green-500/10 p-2 rounded-md">
                    <ArrowRightLeft className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <h4 className="font-bold text-foreground">Handoff (Transferência)</h4>
                    <p className="text-sm text-muted-foreground">
                      Continuidade fluida. Um agente transfere a conversa para outro (ou para um humano) 
                      mantendo todo o contexto e histórico.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="pt-4">
                <Button variant="outline" className="gap-2">
                  Criar Workflow <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="flex-1 relative">
              <div className="absolute inset-0 bg-gradient-to-bl from-accent/20 to-primary/20 rounded-2xl blur-2xl -z-10" />
              <div className="bg-card border border-border rounded-2xl shadow-2xl overflow-hidden">
                <div className="bg-muted/50 p-3 border-b flex gap-2">
                  <div className="h-3 w-3 rounded-full bg-red-500/50" />
                  <div className="h-3 w-3 rounded-full bg-yellow-500/50" />
                  <div className="h-3 w-3 rounded-full bg-green-500/50" />
                </div>
                <div className="p-8 relative h-[400px] bg-grid-slate-100 dark:bg-grid-slate-900/50 flex items-center justify-center overflow-hidden">
                  <div className="relative w-[500px] h-[350px]">
                    <svg className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-visible">
                       {/* Definitions for markers */}
                       <defs>
                        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                          <polygon points="0 0, 10 3.5, 0 7" fill="currentColor" className="text-muted-foreground/50" />
                        </marker>
                      </defs>
                      
                      {/* Router to Sequential */}
                      <path d="M 250 40 C 250 80, 100 80, 100 120" fill="none" stroke="currentColor" strokeWidth="2" className="text-muted-foreground/50" markerEnd="url(#arrowhead)" />
                      
                      {/* Router to Group */}
                      <path d="M 250 40 C 250 80, 400 80, 400 120" fill="none" stroke="currentColor" strokeWidth="2" className="text-muted-foreground/50" markerEnd="url(#arrowhead)" />

                      {/* Sequential Flow */}
                      <path d="M 100 160 L 100 200" fill="none" stroke="currentColor" strokeWidth="2" className="text-muted-foreground/50" markerEnd="url(#arrowhead)" />
                      
                      {/* Sequential to Handoff */}
                      <path d="M 100 240 C 100 280, 250 280, 250 300" fill="none" stroke="currentColor" strokeWidth="2" className="text-muted-foreground/50" strokeDasharray="4" markerEnd="url(#arrowhead)" />

                      {/* Group Chat Connections (Triangle) */}
                      <path d="M 370 140 L 430 140" fill="none" stroke="currentColor" strokeWidth="1" className="text-accent/50" />
                      <path d="M 430 140 L 400 190" fill="none" stroke="currentColor" strokeWidth="1" className="text-accent/50" />
                      <path d="M 400 190 L 370 140" fill="none" stroke="currentColor" strokeWidth="1" className="text-accent/50" />

                    </svg>

                    {/* Router Node (Top) */}
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 bg-background border-2 border-primary rounded-lg p-2 shadow-lg z-20 flex flex-col items-center text-center">
                        <div className="flex items-center gap-2">
                            <GitMerge className="h-4 w-4 text-primary" />
                            <span className="text-xs font-bold">Roteador</span>
                        </div>
                    </div>

                    {/* Sequential Branch (Left) */}
                    <div className="absolute top-[120px] left-[50px] w-28 bg-background border border-border rounded-lg p-2 shadow-md z-10 text-center">
                        <div className="text-[10px] font-bold mb-1">Agente Pesquisa</div>
                        <div className="h-1 w-full bg-primary/20 rounded-full"></div>
                    </div>
                    
                    <div className="absolute top-[200px] left-[50px] w-28 bg-background border border-border rounded-lg p-2 shadow-md z-10 text-center">
                        <div className="text-[10px] font-bold mb-1">Agente Resumo</div>
                        <div className="h-1 w-full bg-primary/20 rounded-full"></div>
                    </div>

                    {/* Group Chat Branch (Right) */}
                    <div className="absolute top-[110px] right-[50px] w-40 h-40 rounded-full border-2 border-dashed border-accent/30 flex items-center justify-center bg-accent/5">
                        <div className="absolute top-2 text-[10px] font-bold text-accent">Group Chat</div>
                    </div>
                    
                    {/* Group Nodes */}
                    <div className="absolute top-[130px] right-[120px] w-10 h-10 rounded-full bg-background border border-accent flex items-center justify-center shadow-sm z-10">
                        <Users className="h-4 w-4 text-accent" />
                    </div>
                    <div className="absolute top-[130px] right-[60px] w-10 h-10 rounded-full bg-background border border-accent flex items-center justify-center shadow-sm z-10">
                        <Brain className="h-4 w-4 text-accent" />
                    </div>
                    <div className="absolute top-[180px] right-[90px] w-10 h-10 rounded-full bg-background border border-accent flex items-center justify-center shadow-sm z-10">
                        <MessageSquare className="h-4 w-4 text-accent" />
                    </div>

                    {/* Handoff Node (Bottom Center) */}
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-36 bg-background border-2 border-green-500 rounded-lg p-2 shadow-lg z-20 flex flex-col items-center text-center animate-pulse">
                        <div className="flex items-center gap-2">
                            <ArrowRightLeft className="h-4 w-4 text-green-500" />
                            <span className="text-xs font-bold text-green-600">Handoff Humano</span>
                        </div>
                        <div className="text-[9px] text-muted-foreground mt-1">Transferindo contexto...</div>
                    </div>

                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">O que você pode construir?</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto mb-12">
            Da automação de tarefas rotineiras à análise complexa de riscos, a MAIA oferece 
            os blocos de construção para transformar a operação da Mapfre.
          </p>
          
          <div className="grid md:grid-cols-3 gap-8">
            {/* Use Case 1: Comparador */}
            <div className="bg-card border rounded-xl p-6 text-left hover:border-primary/50 transition-all hover:-translate-y-1 shadow-sm hover:shadow-md">
              <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                <FileDiff className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-bold mb-2">Comparador de Contratos</h3>
              <p className="text-muted-foreground text-sm mb-4 h-20">
                Identifica divergências entre versões de apólices ou contratos de resseguro, 
                destacando alterações de cláusulas e valores automaticamente.
              </p>
              <div className="bg-muted/50 rounded-lg p-3 text-xs font-mono text-muted-foreground border border-border/50">
                <div className="flex gap-2 mb-1">
                  <span className="text-green-600">+</span>
                  <span>Cláusula 4.2 (Adicionada)</span>
                </div>
                <div className="flex gap-2">
                  <span className="text-red-500">-</span>
                  <span>Franquia: R$ 2.000 (Removida)</span>
                </div>
              </div>
            </div>

            {/* Use Case 2: Extrator */}
            <div className="bg-card border rounded-xl p-6 text-left hover:border-accent/50 transition-all hover:-translate-y-1 shadow-sm hover:shadow-md">
              <div className="h-12 w-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4">
                <Database className="h-6 w-6 text-accent" />
              </div>
              <h3 className="text-lg font-bold mb-2">Extrator de Dados</h3>
              <p className="text-muted-foreground text-sm mb-4 h-20">
                Transforma documentos não estruturados (e-mails, PDFs, imagens) em 
                JSON estruturado pronto para integração com sistemas legados.
              </p>
              <div className="bg-muted/50 rounded-lg p-3 text-xs font-mono text-muted-foreground border border-border/50">
                <span className="text-blue-500">{"{"}</span><br/>
                &nbsp;&nbsp;"placa": "ABC-1234",<br/>
                &nbsp;&nbsp;"valor": 1500.00<br/>
                <span className="text-blue-500">{"}"}</span>
              </div>
            </div>

            {/* Use Case 3: Subscrição */}
            <div className="bg-card border rounded-xl p-6 text-left hover:border-orange-500/50 transition-all hover:-translate-y-1 shadow-sm hover:shadow-md">
              <div className="h-12 w-12 rounded-xl bg-orange-500/10 flex items-center justify-center mb-4">
                <Scale className="h-6 w-6 text-orange-500" />
              </div>
              <h3 className="text-lg font-bold mb-2">Assistente de Subscrição</h3>
              <p className="text-muted-foreground text-sm mb-4 h-20">
                Analisa perfis de risco complexos cruzando dados internos, bureaus de crédito 
                e notícias de mercado para sugerir um score de aceitação.
              </p>
              <div className="bg-muted/50 rounded-lg p-3 text-xs font-mono text-muted-foreground border border-border/50">
                &gt; Score de Risco: 85/100<br/>
                &gt; Recomendação: <span className="text-green-600 font-bold">Aprovar</span>
              </div>
            </div>

            {/* Use Case 4: Auditoria de Calls */}
            <div className="bg-card border rounded-xl p-6 text-left hover:border-purple-500/50 transition-all hover:-translate-y-1 shadow-sm hover:shadow-md">
              <div className="h-12 w-12 rounded-xl bg-purple-500/10 flex items-center justify-center mb-4">
                <Headphones className="h-6 w-6 text-purple-500" />
              </div>
              <h3 className="text-lg font-bold mb-2">Auditoria de Atendimento</h3>
              <p className="text-muted-foreground text-sm mb-4 h-20">
                Transcreve e analisa 100% das chamadas do contact center, identificando 
                sentimento do cliente e conformidade com scripts regulatórios.
              </p>
              <div className="bg-muted/50 rounded-lg p-3 text-xs font-mono text-muted-foreground border border-border/50">
                &gt; Sentimento: <span className="text-red-500">Negativo</span><br/>
                &gt; Alerta: Protocolo não informado.<br/>
                &gt; Risco Legal: <span className="text-yellow-600">Médio</span>
              </div>
            </div>

            {/* Use Case 5: Triagem de Email */}
            <div className="bg-card border rounded-xl p-6 text-left hover:border-blue-400/50 transition-all hover:-translate-y-1 shadow-sm hover:shadow-md">
              <div className="h-12 w-12 rounded-xl bg-blue-400/10 flex items-center justify-center mb-4">
                <Mail className="h-6 w-6 text-blue-400" />
              </div>
              <h3 className="text-lg font-bold mb-2">Triagem Inteligente</h3>
              <p className="text-muted-foreground text-sm mb-4 h-20">
                Lê caixas de entrada departamentais, classifica a urgência, extrai números 
                de apólice e encaminha para a fila correta automaticamente.
              </p>
              <div className="bg-muted/50 rounded-lg p-3 text-xs font-mono text-muted-foreground border border-border/50">
                &gt; Assunto: "Sinistro Urgente"<br/>
                &gt; Classificação: <span className="text-primary font-bold">Perda Total</span><br/>
                &gt; Ação: Fila Prioritária
              </div>
            </div>

            {/* Use Case 6: Investigação de Fraude */}
            <div className="bg-card border rounded-xl p-6 text-left hover:border-red-500/50 transition-all hover:-translate-y-1 shadow-sm hover:shadow-md">
              <div className="h-12 w-12 rounded-xl bg-red-500/10 flex items-center justify-center mb-4">
                <Search className="h-6 w-6 text-red-500" />
              </div>
              <h3 className="text-lg font-bold mb-2">Investigador de Fraudes</h3>
              <p className="text-muted-foreground text-sm mb-4 h-20">
                Cruza dados do relato do sinistro com metadados de fotos, condições 
                climáticas históricas e redes sociais para apontar inconsistências.
              </p>
              <div className="bg-muted/50 rounded-lg p-3 text-xs font-mono text-muted-foreground border border-border/50">
                &gt; Relato: "Chuva forte"<br/>
                &gt; Clima (API): <span className="text-yellow-600">Ensolarado</span><br/>
                &gt; Score Fraude: <span className="text-red-600 font-bold">Alta Probabilidade</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8 mt-auto bg-muted/20">
        <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-primary">MAIA</span>
            <span className="text-muted-foreground text-sm">© 2025 Mapfre Inteligência Artificial</span>
          </div>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <a href="#" className="hover:text-primary transition-colors">Termos de Uso</a>
            <a href="#" className="hover:text-primary transition-colors">Privacidade</a>
            <a href="#" className="hover:text-primary transition-colors">Suporte</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
