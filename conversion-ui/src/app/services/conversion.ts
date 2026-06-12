import { Injectable, signal, computed } from '@angular/core';

export interface Technology {
  id: string;
  label: string;
  icon: string;
  description: string;
  tags: string[];
  color: string;
}

export interface ConversionPath {
  source: Technology;
  target: Technology;
  stages: string[];
  estimatedFiles: string;
  complexity: 'Low' | 'Medium' | 'High';
}

export const SOURCE_TECHNOLOGIES: Technology[] = [
  { id: 'vbscript',     label: 'VBScript',          icon: '📜', description: 'Classic VBScript Subs, Functions, and COM object usage',          tags: ['Sub', 'Function', 'ADODB', 'WScript'],           color: '#f85149' },
  { id: 'classic-asp',  label: 'Classic ASP',        icon: '🌐', description: 'Server-side ASP with Response.Write and inline SQL',             tags: ['Response.Write', 'Request.Form', 'Session[]', 'ADO'], color: '#d29922' },
  { id: 'aspx',         label: 'ASPX / WebForms',    icon: '🖥️', description: 'ASP.NET WebForms with code-behind and server controls',          tags: ['CodeBehind', 'GridView', 'UpdatePanel', 'ViewState'], color: '#ffa657' },
  { id: 'winforms',     label: 'WinForms',           icon: '🪟', description: 'Windows Forms desktop apps with event-driven UI',               tags: ['Form', 'Button_Click', 'DataGridView', 'ADO.NET'],    color: '#d2a8ff' },
  { id: 'wcf',          label: 'WCF Service',        icon: '🔌', description: 'Windows Communication Foundation SOAP services',                tags: ['ServiceContract', 'OperationContract', 'SOAP', 'WSDL'], color: '#79c0ff' },
];

export const TARGET_TECHNOLOGIES: Technology[] = [
  { id: 'dotnet-core',  label: '.NET Core C#',       icon: '⚙️', description: 'Modern sealed services with EF Core, async/await, and DI',      tags: ['sealed', 'async Task', 'EF Core', 'ILogger'],     color: '#3fb950' },
  { id: 'angular',      label: 'Angular',            icon: '🅰️', description: 'TypeScript SPA with standalone components and HttpClient',       tags: ['Component', 'Service', 'HttpClient', 'Signals'],  color: '#f85149' },
  { id: 'react',        label: 'React',              icon: '⚛️', description: 'Functional components with hooks, TypeScript, and Vite',          tags: ['useState', 'useEffect', 'TSX', 'React Query'],    color: '#58a6ff' },
  { id: 'blazor',       label: 'Blazor',             icon: '🔥', description: 'C# Razor components running on WebAssembly or Server',           tags: ['@page', 'EventCallback', 'CascadingValue', 'WASM'], color: '#bc8cff' },
  { id: 'mvc-razor',    label: 'MVC + Razor',        icon: '🗂️', description: 'Controller + ViewModel + Razor View with tag helpers',           tags: ['Controller', 'ViewModel', '@model', 'AntiForgery'], color: '#58a6ff' },
  { id: 'minimal-api',  label: 'Minimal API',        icon: '⚡', description: 'Lightweight .NET 8 endpoints with OpenAPI and DI',               tags: ['MapGet', 'MapPost', 'IResult', 'OpenAPI'],        color: '#3fb950' },
];

const COMPLEXITY_MAP: Record<string, Record<string, ConversionPath['complexity']>> = {
  'vbscript':    { 'dotnet-core': 'Medium', 'angular': 'High',   'react': 'High',   'blazor': 'Medium', 'mvc-razor': 'Medium', 'minimal-api': 'Medium' },
  'classic-asp': { 'dotnet-core': 'Medium', 'angular': 'High',   'react': 'High',   'blazor': 'Medium', 'mvc-razor': 'Low',    'minimal-api': 'Medium' },
  'aspx':        { 'dotnet-core': 'Medium', 'angular': 'High',   'react': 'High',   'blazor': 'Low',    'mvc-razor': 'Low',    'minimal-api': 'Medium' },
  'winforms':    { 'dotnet-core': 'Low',    'angular': 'High',   'react': 'High',   'blazor': 'Medium', 'mvc-razor': 'Medium', 'minimal-api': 'Low'    },
  'wcf':         { 'dotnet-core': 'Low',    'angular': 'Medium', 'react': 'Medium', 'blazor': 'Low',    'mvc-razor': 'Low',    'minimal-api': 'Low'    },
};

const STAGES_MAP: Record<string, string[]> = {
  'vbscript→dotnet-core':    ['Extract Subs / Functions', 'Assemble Context + Schema', 'Generate sealed Services', 'Validate Patterns', 'Recover & Fix'],
  'vbscript→angular':        ['Extract Subs / Functions', 'Map to Service Methods', 'Generate Angular Services', 'Generate Components', 'Validate & Fix'],
  'vbscript→react':          ['Extract Subs / Functions', 'Map to Hook Logic', 'Generate React Components', 'Generate API Layer', 'Validate & Fix'],
  'classic-asp→dotnet-core': ['Extract DAL + UI Layers', 'Assemble Context', 'Generate Controller + ViewModel', 'Generate Razor View', 'Validate & Recover'],
  'classic-asp→mvc-razor':   ['Extract ASP Layers', 'Assemble MVC Context', 'Generate Controller', 'Generate ViewModel + View', 'Validate'],
  'classic-asp→angular':     ['Extract DAL + UI Layers', 'Map to Angular Architecture', 'Generate Components', 'Generate HTTP Services', 'Validate & Fix'],
  'aspx→blazor':             ['Parse WebForms Structure', 'Map Controls to Razor', 'Generate Blazor Pages', 'Validate & Recover', 'Review'],
  'aspx→angular':            ['Parse WebForms Structure', 'Map Controls to Components', 'Generate Angular Components', 'Generate Services', 'Validate'],
  'aspx→mvc-razor':          ['Parse WebForms Structure', 'Extract Code-Behind Logic', 'Generate Controllers', 'Generate Razor Views', 'Validate'],
  'wcf→minimal-api':         ['Parse ServiceContract', 'Map Operations to Endpoints', 'Generate Minimal API', 'Add OpenAPI Spec', 'Validate'],
  'wcf→dotnet-core':         ['Parse ServiceContract', 'Map to Interface + Service', 'Generate sealed Service', 'Validate', 'Recover'],
  'default':                 ['Extract Source Units', 'Assemble Context Packages', 'Generate Target Code', 'Validate Output', 'Recover & Review'],
};

const FILES_MAP: Record<string, string> = {
  'classic-asp→mvc-razor':   '1 ASP → 3–4 files (Controller, ViewModel, View, Service)',
  'classic-asp→angular':     '1 ASP → 4–5 files (Component, Service, Model, HTML, SCSS)',
  'vbscript→dotnet-core':    '1 VBS → 1–2 files (sealed Service + optional Interface)',
  'aspx→blazor':             '1 ASPX → 2 files (Razor Component + code-behind)',
  'aspx→angular':            '1 ASPX → 3–4 files (Component, Module, Service, HTML)',
  'wcf→minimal-api':         '1 WCF → 1 file (Minimal API endpoints file)',
};

@Injectable({ providedIn: 'root' })
export class ConversionService {
  selectedSource = signal<Technology | null>(null);
  selectedTarget = signal<Technology | null>(null);
  currentStep    = signal<1 | 2 | 3>(1);

  canProceed = computed(() => {
    const step = this.currentStep();
    if (step === 1) return this.selectedSource() !== null;
    if (step === 2) return this.selectedTarget() !== null;
    return true;
  });

  conversionPath = computed<ConversionPath | null>(() => {
    const src = this.selectedSource();
    const tgt = this.selectedTarget();
    if (!src || !tgt) return null;
    const key = `${src.id}→${tgt.id}`;
    return {
      source: src,
      target: tgt,
      stages: STAGES_MAP[key] ?? STAGES_MAP['default'],
      estimatedFiles: FILES_MAP[key] ?? '1 source → 2–4 output files',
      complexity: COMPLEXITY_MAP[src.id]?.[tgt.id] ?? 'Medium',
    };
  });

  selectSource(tech: Technology) { this.selectedSource.set(tech); }
  selectTarget(tech: Technology) { this.selectedTarget.set(tech); }
  goToStep(step: 1 | 2 | 3)     { this.currentStep.set(step); }
  next() { const s = this.currentStep(); if (s < 3) this.currentStep.set((s + 1) as 1|2|3); }
  back() { const s = this.currentStep(); if (s > 1) this.currentStep.set((s - 1) as 1|2|3); }
  reset() { this.selectedSource.set(null); this.selectedTarget.set(null); this.currentStep.set(1); }
}
