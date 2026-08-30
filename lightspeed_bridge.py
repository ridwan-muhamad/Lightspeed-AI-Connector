#!/usr/bin/env python3
"""
Red Hat Enterprise AI Assistant & OpenAI-compatible Bridge for OpenCode
Backend Engine: Red Hat Lightspeed Core via D-Bus (clad.service)

Features:
  - Full Agentic Tool Calling & Terminal Execution support for OpenCode CLI
  - Enterprise Web Chat UI with Red Hat Product Categorized Prompts (RHEL, OCP, RHOSP, RHOSO, Ansible, Satellite)
  - Red Hat Certification Hub (RHCSA, RHCE, OpenShift EX280, AI Examiner)
  - Collapsible / Hideable Sidebar with Local Storage Preference
  - Raw Log Root-Cause Analyzer Modal (paste journalctl, dmesg, oc logs)
  - Multi-Session Chat Management (Local Persistence, Export to Markdown)
  - Universal OpenAI-compatible API (/v1/chat/completions, /v1/models)
"""

import json
import logging
import os
import platform
import re
import sys
import time
import uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional, Tuple

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("RH-Lightspeed-Bridge")

# D-Bus integration with Red Hat Lightspeed (clad.service)
try:
    from command_line_assistant.dbus.client import DbusClient
    from command_line_assistant.dbus.structures.chat import (
        Question,
        Response,
        SystemInfo,
        StdinInput,
        AttachmentInput,
        TerminalInput,
    )
    HAS_DBUS = True
except ImportError as e:
    logger.warning("command_line_assistant package not found in this environment: %s", e)
    HAS_DBUS = False


class LightspeedClient:
    def __init__(self):
        if not HAS_DBUS:
            self.user_id = "mock-user"
            self.os_info = None
            logger.warning("Running in mock mode (D-Bus unavailable)")
            return

        self.dbus_client = DbusClient()
        self.uid = os.getuid()
        self.user_id = self.dbus_client.user_proxy.GetUserId(self.uid)
        logger.info(f"Initialized LightspeedClient (UID: {self.uid}, UserID: {self.user_id})")

        uname = platform.uname()
        self.os_info = SystemInfo(
            os="Red Hat Enterprise Linux",
            version="10.0",
            arch=uname.machine,
            id="rhel"
        )

    def query(self, prompt: str) -> str:
        if not HAS_DBUS:
            return f"[Mock Lightspeed Response]: Received prompt: {prompt}"

        q = Question(
            message=prompt,
            stdin=StdinInput(""),
            attachment=AttachmentInput("", ""),
            terminal=TerminalInput(""),
            systeminfo=self.os_info
        )
        resp_struct = self.dbus_client.chat_proxy.AskQuestion(self.user_id, q.structure())
        response = Response.from_structure(resp_struct)
        return response.message


lightspeed = LightspeedClient()

# Enterprise SysAdmin Web Interface
WEB_UI_HTML = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Assistant for Linux & DevOps Administrator</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        rh: {
                            red: '#EE0000',
                            darkred: '#A30000',
                            black: '#151515',
                            dark: '#0F1216',
                            panel: '#1B1D21',
                            card: '#212429',
                            border: '#383B40',
                            accent: '#4B88EC'
                        }
                    }
                }
            }
        }
    </script>
    <!-- Markdown & Highlight.js -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body { font-family: 'Red Hat Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .code-font { font-family: 'Red Hat Mono', 'Fira Code', 'Courier New', monospace; }
        .prose pre { background: #151515 !important; border-radius: 8px; padding: 14px; position: relative; margin: 12px 0; border: 1px solid #383b40; }
        .prose code { color: #58a6ff; font-family: 'Fira Code', 'Courier New', monospace; font-size: 0.85rem; }
        .prose p { margin-bottom: 0.85rem; line-height: 1.65; }
        .prose p:last-child { margin-bottom: 0; }
        .prose ul, .prose ol { margin-left: 1.5rem; margin-bottom: 0.85rem; }
        .prose li { margin-bottom: 0.35rem; }
        .prose table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 0.85rem; }
        .prose th, .prose td { border: 1px solid #383b40; padding: 8px 12px; }
        .prose th { background: #212429; color: #f8fafc; font-weight: 600; }
        .prose tr:nth-child(even) { background: #1b1d21; }
        .prose blockquote { border-left: 4px solid #EE0000; padding-left: 12px; margin: 10px 0; color: #94a3b8; }
        
        /* High Contrast Hyperlinks & Sources */
        .prose a, .source-link {
            color: #38bdf8 !important;
            text-decoration: underline !important;
            text-decoration-color: rgba(56, 189, 248, 0.45) !important;
            text-underline-offset: 3px !important;
            font-weight: 600 !important;
            display: inline-flex !important;
            align-items: center !important;
            background: rgba(56, 189, 248, 0.1) !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            padding: 2px 7px !important;
            border-radius: 6px !important;
            margin: 2px 2px 2px 0 !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            word-break: break-all;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
        }
        .prose a:hover, .source-link:hover {
            color: #ffffff !important;
            background: #0284c7 !important;
            border-color: #38bdf8 !important;
            text-decoration: none !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.4);
        }
        .source-domain {
            color: #bae6fd;
            font-weight: 700;
            margin-right: 4px;
        }
        .source-path {
            color: #e0f2fe;
            font-weight: 400;
            opacity: 0.9;
        }
        .source-section-header {
            margin-top: 1.25rem;
            margin-bottom: 0.6rem;
            padding: 6px 10px;
            background: rgba(238, 0, 0, 0.1);
            border-left: 3px solid #EE0000;
            border-radius: 0 6px 6px 0;
            color: #fca5a5;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: flex;
            align-items: center;
        }

        .copy-btn {
            position: absolute; top: 8px; right: 8px;
            background: #2b2e35; color: #cbd5e1; border: 1px solid #3f444e;
            padding: 3px 9px; border-radius: 5px; font-size: 11px; cursor: pointer;
            transition: all 0.2s ease;
        }
        .copy-btn:hover { background: #EE0000; color: #ffffff; border-color: #EE0000; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f1216; }
        ::-webkit-scrollbar-thumb { background: #2b2e35; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #3f444e; }
        .active-tab { border-color: #EE0000 !important; color: #ffffff !important; background: rgba(238, 0, 0, 0.1) !important; }
        .active-session { background: #2b2e35 !important; border-left: 3px solid #EE0000 !important; }
    </style>
</head>
<body class="bg-rh-dark text-slate-100 flex flex-col h-screen overflow-hidden select-none">

    <!-- Top Enterprise Header -->
    <header class="bg-rh-panel border-b border-rh-border px-4 sm:px-5 py-2.5 flex items-center justify-between z-20 shadow-md">
        <!-- Brand & Product -->
        <div class="flex items-center space-x-3">
            <button onclick="toggleSidebar()" class="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-rh-card transition focus:outline-none" title="Toggle Product Categories / Sidebar">
                <i class="fa-solid fa-bars-staggered text-sm"></i>
            </button>
            <div class="w-9 h-9 rounded-xl bg-rh-red flex items-center justify-center shadow-lg shadow-red-950/60 flex-shrink-0">
                <i class="fa-solid fa-hat-cowboy text-white text-lg"></i>
            </div>
            <div>
                <div class="flex items-center space-x-2">
                    <h1 class="font-bold text-sm sm:text-base tracking-wide text-white">Rdw</h1>
                    <span class="bg-red-500/15 text-red-400 text-[10px] px-2 py-0.5 rounded border border-red-500/30 font-semibold tracking-wider uppercase">RHEL AI</span>
                </div>
                <p class="text-[11px] text-slate-400 hidden sm:block">AI Assistant for Linux & DevOps Administrator</p>
            </div>
        </div>

        <!-- Clean Status Badge -->
        <div class="hidden sm:flex items-center space-x-2 bg-rh-card/80 px-3 py-1.5 rounded-lg border border-rh-border text-xs text-slate-300">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Model: <strong class="text-white font-mono">rhel-lightspeed</strong></span>
            <span class="text-slate-500">•</span>
            <span class="text-emerald-400 font-medium">Ready</span>
        </div>

        <!-- Action Tools -->
        <div class="flex items-center space-x-2">
            <button onclick="switchCategory('cert')" class="bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 shadow-sm" title="Red Hat Certification Prep (RHCSA, RHCE, OpenShift)">
                <i class="fa-solid fa-graduation-cap text-amber-400"></i>
                <span class="hidden md:inline">Cert Prep</span>
            </button>
            <button onclick="toggleLogModal()" class="bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 text-xs font-medium transition flex items-center space-x-1.5 shadow-sm" title="Analyze Raw Logs">
                <i class="fa-solid fa-file-code text-amber-400"></i>
                <span>Log Analyzer</span>
            </button>
            <button onclick="exportCurrentSession()" class="text-slate-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-xs transition" title="Export Session to Markdown">
                <i class="fa-solid fa-download"></i>
            </button>
            <button onclick="createNewSession()" class="bg-rh-red hover:bg-red-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 shadow-md shadow-red-950/40">
                <i class="fa-solid fa-plus"></i>
                <span class="hidden sm:inline">New Thread</span>
            </button>
        </div>
    </header>

    <!-- Main Workspace -->
    <div class="flex-1 flex overflow-hidden relative">

        <!-- Left Sidebar: Product Categories & Quick Prompts -->
        <aside id="mainSidebar" class="w-80 bg-rh-panel border-r border-rh-border flex flex-col justify-between overflow-y-auto transition-all duration-200 flex-shrink-0">
            
            <!-- Category Tabs Header -->
            <div class="p-3 border-b border-rh-border">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Product Categories</span>
                    <button onclick="toggleSidebar()" class="text-slate-500 hover:text-slate-300 text-xs p-1 rounded hover:bg-rh-card" title="Hide Sidebar">
                        <i class="fa-solid fa-chevron-left"></i>
                    </button>
                </div>
                <div class="grid grid-cols-2 gap-1.5 text-xs">
                    <button onclick="switchCategory('rhel')" id="tab-rhel" class="category-tab active-tab p-2 rounded-lg border border-rh-border text-left font-medium transition flex items-center space-x-2">
                        <i class="fa-brands fa-linux text-red-500"></i>
                        <span>RHEL Core</span>
                    </button>
                    <button onclick="switchCategory('ocp')" id="tab-ocp" class="category-tab p-2 rounded-lg border border-rh-border text-left text-slate-400 hover:text-white font-medium transition flex items-center space-x-2">
                        <i class="fa-solid fa-cubes text-red-400"></i>
                        <span>OpenShift</span>
                    </button>
                    <button onclick="switchCategory('cloud')" id="tab-cloud" class="category-tab p-2 rounded-lg border border-rh-border text-left text-slate-400 hover:text-white font-medium transition flex items-center space-x-2">
                        <i class="fa-solid fa-cloud text-cyan-400"></i>
                        <span>RHOSO / RHOSP</span>
                    </button>
                    <button onclick="switchCategory('ansible')" id="tab-ansible" class="category-tab p-2 rounded-lg border border-rh-border text-left text-slate-400 hover:text-white font-medium transition flex items-center space-x-2">
                        <i class="fa-solid fa-terminal text-emerald-400"></i>
                        <span>Ansible & Satellite</span>
                    </button>
                    <button onclick="switchCategory('cert')" id="tab-cert" class="col-span-2 category-tab p-2 rounded-lg border border-rh-border text-left text-slate-400 hover:text-white font-medium transition flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <i class="fa-solid fa-graduation-cap text-amber-400"></i>
                            <span>Red Hat Certifications</span>
                        </div>
                        <span class="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-mono uppercase font-bold border border-amber-500/30">RHCSA • RHCE</span>
                    </button>
                </div>
            </div>

            <!-- Dynamic Prompt List per Category -->
            <div class="flex-1 p-3 overflow-y-auto space-y-2" id="promptContainer">
                <!-- Injected via JavaScript -->
            </div>

            <!-- Session Threads List -->
            <div class="p-3 border-t border-rh-border bg-rh-card/50 max-h-48 flex flex-col">
                <div class="flex items-center justify-between mb-1.5">
                    <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Saved Incidents</span>
                    <button onclick="clearAllSessions()" class="text-[10px] text-red-400 hover:underline">Clear All</button>
                </div>
                <div class="flex-1 overflow-y-auto space-y-1" id="sessionList">
                    <!-- Session list rendered via JS -->
                </div>
            </div>
        </aside>

        <!-- Right Main Chat Workspace -->
        <main class="flex-1 flex flex-col justify-between bg-rh-dark overflow-hidden">

            <!-- Chat Message Thread -->
            <div id="chatMessages" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
                <!-- Welcome Hub (Default State) -->
                <div id="welcomeHub" class="max-w-4xl mx-auto py-8 px-4">
                    <div class="text-center mb-8">
                        <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-rh-darkred to-rh-red text-white flex items-center justify-center mx-auto mb-4 shadow-xl shadow-red-950/60">
                            <i class="fa-solid fa-hat-cowboy text-2xl"></i>
                        </div>
                        <h2 class="text-2xl font-bold text-white tracking-wide mb-2">Red Hat Lightspeed AI Portal</h2>
                        <p class="text-sm text-slate-400 max-w-xl mx-auto">
                            Asisten AI cerdas untuk tim Senior Linux Administrator, SRE, dan Cloud Infrastructure Engineer. Silakan pilih template di bawah atau ketik langsung pertanyaan/kasus teknis Anda.
                        </p>
                    </div>

                    <!-- Enterprise Quick Scenario Cards -->
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                        
                        <!-- RHEL Storage & HA -->
                        <div class="bg-rh-panel hover:bg-rh-card p-4 rounded-xl border border-rh-border hover:border-red-500/50 cursor-pointer transition flex flex-col justify-between group shadow-sm"
                             onclick="usePrompt('RHEL', 'Buatkan arsitektur dan langkah konfigurasi High Availability Cluster 2-Node menggunakan Pacemaker, Corosync, dan PCS dengan QDevice witness di RHEL.')">
                            <div>
                                <div class="w-8 h-8 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                                    <i class="fa-solid fa-heart-pulse"></i>
                                </div>
                                <h3 class="font-semibold text-sm text-slate-200 mb-1">RHEL High Availability</h3>
                                <p class="text-xs text-slate-400">Pacemaker, Corosync, PCS clustering & fencing configuration.</p>
                            </div>
                            <span class="text-[11px] text-red-400 font-medium mt-3 flex items-center">Gunakan Template <i class="fa-solid fa-arrow-right ml-1 text-[10px]"></i></span>
                        </div>

                        <!-- OpenShift Ingress & OSD -->
                        <div class="bg-rh-panel hover:bg-rh-card p-4 rounded-xl border border-rh-border hover:border-red-500/50 cursor-pointer transition flex flex-col justify-between group shadow-sm"
                             onclick="usePrompt('OCP', 'Bagaimana cara mendiagnosa Pod stuck di ContainerCreating atau CrashLoopBackOff pada OpenShift Container Platform (OCP)? Berikan checklist kubectl/oc command.')">
                            <div>
                                <div class="w-8 h-8 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                                    <i class="fa-solid fa-cubes"></i>
                                </div>
                                <h3 class="font-semibold text-sm text-slate-200 mb-1">OpenShift Diagnostics</h3>
                                <p class="text-xs text-slate-400">Troubleshooting Pod CrashLoop, MachineConfig, & Operator health.</p>
                            </div>
                            <span class="text-[11px] text-red-400 font-medium mt-3 flex items-center">Gunakan Template <i class="fa-solid fa-arrow-right ml-1 text-[10px]"></i></span>
                        </div>

                        <!-- OpenStack RHOSO / RHOSP -->
                        <div class="bg-rh-panel hover:bg-rh-card p-4 rounded-xl border border-rh-border hover:border-red-500/50 cursor-pointer transition flex flex-col justify-between group shadow-sm"
                             onclick="usePrompt('Cloud', 'Jelaskan perbedaan arsitektur RHOSP (TripleO/Director) dengan RHOSO (Red Hat OpenStack Services on OpenShift) dan cara troubleshooting Nova compute agent.')">
                            <div>
                                <div class="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                                    <i class="fa-solid fa-cloud"></i>
                                </div>
                                <h3 class="font-semibold text-sm text-slate-200 mb-1">RHOSO / RHOSP Cloud</h3>
                                <p class="text-xs text-slate-400">OpenStack control plane on OCP, Neutron network & Ceph storage.</p>
                            </div>
                            <span class="text-[11px] text-red-400 font-medium mt-3 flex items-center">Gunakan Template <i class="fa-solid fa-arrow-right ml-1 text-[10px]"></i></span>
                        </div>

                        <!-- Ansible Playbook Generation -->
                        <div class="bg-rh-panel hover:bg-rh-card p-4 rounded-xl border border-rh-border hover:border-red-500/50 cursor-pointer transition flex flex-col justify-between group shadow-sm"
                             onclick="usePrompt('Ansible', 'Buatkan Ansible Playbook yang idempotent dan production-ready untuk CIS Benchmark hardening di RHEL 9/10.')">
                            <div>
                                <div class="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                                    <i class="fa-solid fa-code"></i>
                                </div>
                                <h3 class="font-semibold text-sm text-slate-200 mb-1">Ansible Hardening</h3>
                                <p class="text-xs text-slate-400">Automasi CIS Benchmark, role structure, & idempotency standard.</p>
                            </div>
                            <span class="text-[11px] text-red-400 font-medium mt-3 flex items-center">Gunakan Template <i class="fa-solid fa-arrow-right ml-1 text-[10px]"></i></span>
                        </div>

                        <!-- SELinux & Audit Policy -->
                        <div class="bg-rh-panel hover:bg-rh-card p-4 rounded-xl border border-rh-border hover:border-red-500/50 cursor-pointer transition flex flex-col justify-between group shadow-sm"
                             onclick="usePrompt('RHEL', 'Bagaimana cara menganalisa SELinux AVC denial di /var/log/audit/audit.log dan membuat custom policy module dengan audit2allow & semodule?')">
                            <div>
                                <div class="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                                    <i class="fa-solid fa-shield-halved"></i>
                                </div>
                                <h3 class="font-semibold text-sm text-slate-200 mb-1">SELinux Deep Dive</h3>
                                <p class="text-xs text-slate-400">AVC Denial resolution, audit log investigation, & custom TE policies.</p>
                            </div>
                            <span class="text-[11px] text-red-400 font-medium mt-3 flex items-center">Gunakan Template <i class="fa-solid fa-arrow-right ml-1 text-[10px]"></i></span>
                        </div>

                        <!-- Red Hat Certification Hub -->
                        <div class="bg-rh-panel hover:bg-rh-card p-4 rounded-xl border border-amber-500/30 hover:border-amber-500/60 cursor-pointer transition flex flex-col justify-between group shadow-sm bg-gradient-to-b from-amber-500/5 to-transparent"
                             onclick="usePrompt('cert', 'Saya sedang mempersiapkan ujian sertifikasi Red Hat (RHCSA EX200 / RHCE EX294 / OpenShift EX280). Berikan roadmap belajar terstruktur, rangkuman objektif ujian kunci, dan contoh latihan lab praktis.')">
                            <div>
                                <div class="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                                    <i class="fa-solid fa-graduation-cap"></i>
                                </div>
                                <div class="flex items-center space-x-2 mb-1">
                                    <h3 class="font-semibold text-sm text-slate-200">Red Hat Cert Prep</h3>
                                    <span class="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-mono font-bold">RHCSA/RHCE</span>
                                </div>
                                <p class="text-xs text-slate-400">Simulasi lab ujian RHCSA (EX200), RHCE (EX294), OpenShift (EX280), dan AI Examiner grading.</p>
                            </div>
                            <span class="text-[11px] text-amber-400 font-medium mt-3 flex items-center">Buka Lab Simulator <i class="fa-solid fa-arrow-right ml-1 text-[10px]"></i></span>
                        </div>

                        <!-- Kernel Tuning & Sysctl -->
                        <div class="bg-rh-panel hover:bg-rh-card p-4 rounded-xl border border-rh-border hover:border-red-500/50 cursor-pointer transition flex flex-col justify-between group shadow-sm"
                             onclick="usePrompt('rhel', 'Berikan rekomendasi konfigurasi /etc/sysctl.d/ untuk server database high-concurrency (dirty ratio, network backlog, TCP buffer, somaxconn).')">
                            <div>
                                <div class="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                                    <i class="fa-solid fa-sliders"></i>
                                </div>
                                <h3 class="font-semibold text-sm text-slate-200 mb-1">Kernel & Network Tuning</h3>
                                <p class="text-xs text-slate-400">Sysctl performance profiles, TCP window scaling, & I/O scheduler.</p>
                            </div>
                            <span class="text-[11px] text-red-400 font-medium mt-3 flex items-center">Gunakan Template <i class="fa-solid fa-arrow-right ml-1 text-[10px]"></i></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Input Bar -->
            <div class="p-4 bg-rh-panel border-t border-rh-border">
                <div class="max-w-4xl mx-auto">
                    <form id="chatForm" onsubmit="handleSend(event)" class="relative flex items-end bg-rh-dark rounded-xl border border-rh-border focus-within:border-red-500 transition shadow-inner">
                        <textarea id="promptInput" 
                                  rows="1" 
                                  placeholder="Ketik pertanyaan administrasi Red Hat, troubleshooting log, atau playbook request... (Enter kirim, Shift+Enter baris baru)" 
                                  class="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 px-4 py-3.5 pr-20 outline-none resize-none overflow-y-auto max-h-40"
                                  onkeydown="handleKeyDown(event)"
                                  oninput="autoResize(this)"></textarea>
                        
                        <div class="absolute right-2 bottom-2 flex items-center space-x-1">
                            <button type="button" onclick="toggleLogModal()" class="w-8 h-8 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-rh-card flex items-center justify-center transition" title="Paste Raw System Log">
                                <i class="fa-solid fa-file-import text-xs"></i>
                            </button>
                            <button type="submit" id="sendBtn" 
                                     class="w-8 h-8 rounded-lg bg-rh-red hover:bg-red-600 text-white flex items-center justify-center transition disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-red-950/40">
                                <i class="fa-solid fa-paper-plane text-xs"></i>
                            </button>
                        </div>
                    </form>
                    
                    <div class="flex items-center justify-between text-[11px] text-slate-500 mt-2 px-1">
                        <div class="flex items-center space-x-2">
                            <span>Backend: <strong class="text-slate-400 font-mono">rhel-lightspeed</strong></span>
                            <span>•</span>
                            <span>OpenAI API Compatible Gateway</span>
                        </div>
                        <div class="flex items-center space-x-1.5 text-emerald-400">
                            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                            <span>Ready</span>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- Modal: Raw Log Root-Cause Analyzer -->
    <div id="logModal" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
        <div class="bg-rh-panel border border-rh-border rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
            <div class="bg-rh-card px-5 py-3.5 border-b border-rh-border flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <i class="fa-solid fa-file-waveform text-amber-400 text-base"></i>
                    <h3 class="font-bold text-sm text-white">SysAdmin Raw Log Root-Cause Analyzer</h3>
                </div>
                <button onclick="toggleLogModal()" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="p-5 space-y-3">
                <p class="text-xs text-slate-300">
                    Tempelkan cuplikan log mentah dari <code class="code-font text-red-400">journalctl</code>, <code class="code-font text-red-400">dmesg</code>, <code class="code-font text-red-400">/var/log/messages</code>, atau <code class="code-font text-red-400">oc logs</code> untuk dianalisa akar permasalahannya oleh Lightspeed.
                </p>
                <textarea id="rawLogInput" rows="9" 
                          placeholder="Paste output error log di sini... (contoh: Aug 27 18:20:11 kernel: Out of memory: Kill process 1243...)"
                          class="w-full bg-rh-dark border border-rh-border rounded-xl p-3.5 text-xs text-slate-200 code-font placeholder-slate-600 outline-none focus:border-red-500 transition"></textarea>
                
                <div class="flex items-center justify-between pt-2">
                    <span class="text-[11px] text-slate-500">Lightspeed akan menyaring pesan error dan memberikan rekomendasi solusi presisi.</span>
                    <button onclick="submitLogAnalysis()" class="bg-rh-red hover:bg-red-600 text-white px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 shadow-md">
                        <i class="fa-solid fa-magnifying-glass"></i>
                        <span>Analisa Log Sekarang</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Frontend Logic & State Management -->
    <script>
        // Preset Prompts Database by Product Category
        const CATEGORY_PROMPTS = {
            rhel: [
                { title: 'Analisa Log Journalctl', prompt: 'Analisa error dan warning pada systemd journalctl 1 jam terakhir, berikan root cause, dampak pada service, dan langkah mitigasi CLI.' },
                { title: 'LVM Storage & Thin Pool', prompt: 'Bagaimana cara membuat LVM Thin Provisioning pool dengan auto-extension threshold dan membuat LV di RHEL?' },
                { title: 'SELinux AVC Denials', prompt: 'Jelaskan cara mencari AVC denial di audit log dan membuat custom policy module dengan audit2allow.' },
                { title: 'Network Bonding (LACP)', prompt: 'Berikan langkah membuat network bonding mode 802.3ad (LACP) menggunakan nmcli di RHEL 10.' },
                { title: 'Kernel Live Patching', prompt: 'Bagaimana cara memasang kpatch dan memverifikasi CVE mana saja yang telah tertambal tanpa reboot?' }
            ],
            ocp: [
                { title: 'Pod CrashLoop Diagnostics', prompt: 'Berikan checklist lengkap untuk mendiagnosa Pod OpenShift yang mengalami status CrashLoopBackOff atau OOMKilled.' },
                { title: 'Operator Degraded Status', prompt: 'Bagaimana cara melakukan troubleshooting ClusterOperator yang berstatus Degraded pada OpenShift Container Platform (OCP)?' },
                { title: 'MachineConfig & Node Reboot', prompt: 'Jelaskan cara membuat MachineConfig untuk mengubah parameter kernel sysctl di node OpenShift tanpa mengganggu traffic.' },
                { title: 'OpenShift Virtualization', prompt: 'Bagaimana cara mengonfigurasi NetworkAttachmentDefinition (multus) untuk Virtual Machine di OpenShift Virtualization?' }
            ],
            cloud: [
                { title: 'RHOSO Architecture & Nova', prompt: 'Jelaskan arsitektur Red Hat OpenStack Services on OpenShift (RHOSO) dan cara troubleshooting Nova compute agent via OpenShift CR.' },
                { title: 'Ceph Storage OSD Health', prompt: 'Bagaimana cara mendiagnosa Ceph OSD down / degraded pada Red Hat Ceph Storage / RHOSP Cinder backend?' },
                { title: 'Neutron OVN Flow Debugging', prompt: 'Berikan panduan troubleshooting konektivitas VM OpenStack yang menggunakan OVN (Open Virtual Network).' },
                { title: 'TripleO to RHOSO Migration', prompt: 'Apa saja tahap kunci dalam migrasi control plane RHOSP klasik ke RHOSO berbasis container OpenShift?' }
            ],
            ansible: [
                { title: 'Ansible Idempotent Storage Role', prompt: 'Buatkan Ansible Role lengkap dengan tasks/main.yml yang idempotent untuk format disk, LVM, dan mount filesystem.' },
                { title: 'Red Hat Satellite Errata Patching', prompt: 'Tuliskan perintah hammer CLI di Red Hat Satellite untuk mempublikasikan Content View baru dan menerapkan errata keamanan ke Host Collection.' },
                { title: 'AAP Execution Environment', prompt: 'Bagaimana cara membuat custom Execution Environment (EE) menggunakan ansible-builder untuk Ansible Automation Platform (AAP)?' },
                { title: 'Auditd CIS Hardening Playbook', prompt: 'Buatkan playbook Ansible untuk mengonfigurasi rule auditd sesuai standar benchmark keamanan enterprise.' }
            ],
            cert: [
                { 
                    title: '🎯 AI Examiner (Tanya & Nilai Lab)', 
                    prompt: 'Saya ingin melakukan simulasi ujian interaktif sertifikasi Red Hat. Berikan saya SATU soal tugas hands-on (pilihkan antara RHCSA / RHCE / OpenShift EX280) terlebih dahulu. Tunggu jawaban baris perintah CLI saya, kemudian berikan skor kelulusan (0-100), analisis kesalahan (jika ada), dan rekomendasi solusi presisi.' 
                },
                { 
                    title: 'RHCSA (EX200) Full Lab Challenge', 
                    prompt: 'Berikan 1 skenario lab simulasi ujian RHCSA (EX200) lengkap dengan 5 tugas: 1. Konfigurasi LVM (VG & LV 500MB ext4 mount persistent), 2. User & group permission dengan ACL dan sudoers, 3. SELinux port binding untuk httpd non-standar (port 82), 4. Crontab schedule user, 5. Rootless Podman container dengan systemd user service auto-start. Berikan instruksi soal dan kunci jawaban perintah CLI serta verifikasi reboot.' 
                },
                { 
                    title: 'RHCE (EX294) Ansible Exam Tasks', 
                    prompt: 'Buatkan skenario latihan ujian RHCE (EX294): Tuliskan Ansible Playbook yang idempotent untuk: 1. Membuat dynamic MOTD menggunakan template Jinja2, 2. Membuat custom storage LVM pada managed hosts, 3. Konfigurasi web server + firewall, 4. Manajemen user dengan password terenkripsi via ansible-vault. Sertakan kriteria penilaian (grading criteria).' 
                },
                { 
                    title: 'EX280 OpenShift Admin Practice', 
                    prompt: 'Berikan latihan studi kasus ujian Red Hat Certified OpenShift Administrator (EX280): 1. Konfigurasi RBAC (Role, RoleBinding, ServiceAccount), 2. Deploy multi-replica workload dengan PVC storage, 3. Konfigurasi Edge TLS Ingress Route, 4. Buat NetworkPolicy untuk membatasi traffic ingress. Sertakan manifest YAML dan perintah oc CLI.' 
                },
                { 
                    title: 'EX188 Containers & Podman Specialist', 
                    prompt: 'Berikan simulasi soal ujian Red Hat Certified Specialist in Containers (EX188): Buat Containerfile multi-stage yang secure (non-root user, minimal base image), build image dengan podman, konfigurasi environment variables, mount persistent volume, dan generate systemd service unit.' 
                },
                { 
                    title: 'Emergency Recovery & Exam Tips', 
                    prompt: 'Berikan panduan troubleshooting darurat dan tips kecepatan untuk ujian sertifikasi Red Hat: 1. Langkah reset root password via rd.break / init=/bin/bash di GRUB, 2. Memperbaiki sistem jika boot gagal karena kesalahan /etc/fstab, 3. Checklist wajib sebelum menekan tombol submit ujian.' 
                },
                { 
                    title: 'Roadmap Sertifikasi & RHCA Track', 
                    prompt: 'Jelaskan roadmap sertifikasi Red Hat lengkap dari RHCSA (EX200), RHCE (EX294), OpenShift Specialist (EX280, EX380), Cloud & Virtualization (EX318), hingga mencapai level Red Hat Certified Architect (RHCA). Berikan tips memilih track spesialisasi dan referensi resmi https://www.redhat.com/en/services/certifications.' 
                }
            ]
        };

        // State
        let currentCategory = 'rhel';
        let sessions = [];
        let activeSessionId = null;

        // Elements
        const mainSidebar = document.getElementById('mainSidebar');
        const chatMessages = document.getElementById('chatMessages');
        const welcomeHub = document.getElementById('welcomeHub');
        const promptInput = document.getElementById('promptInput');
        const sendBtn = document.getElementById('sendBtn');
        const promptContainer = document.getElementById('promptContainer');
        const sessionList = document.getElementById('sessionList');
        const logModal = document.getElementById('logModal');

        // Initialize App
        window.addEventListener('DOMContentLoaded', () => {
            renderPrompts('rhel');
            loadSessions();
            
            // Restore sidebar state
            const sidebarPref = localStorage.getItem('rh_sidebar_visible');
            if (sidebarPref === 'false') {
                if (mainSidebar) mainSidebar.classList.add('hidden');
            }
        });

        // Sidebar Toggle (Hide/Unhide)
        function toggleSidebar() {
            if (!mainSidebar) return;
            const isHidden = mainSidebar.classList.contains('hidden');
            if (isHidden) {
                mainSidebar.classList.remove('hidden');
                localStorage.setItem('rh_sidebar_visible', 'true');
            } else {
                mainSidebar.classList.add('hidden');
                localStorage.setItem('rh_sidebar_visible', 'false');
            }
        }

        // Marked Renderer & High Contrast Links Configuration
        const customRenderer = new marked.Renderer();
        customRenderer.link = function(href, title, text) {
            let targetHref = typeof href === 'object' ? href.href : href;
            let targetTitle = typeof href === 'object' ? href.title : title;
            let targetText = typeof href === 'object' ? href.text : text;

            if (!targetHref) return targetText || '';

            let label = targetText || targetHref;
            let isUrlLabel = label.startsWith('http://') || label.startsWith('https://');

            if (isUrlLabel) {
                try {
                    const u = new URL(label);
                    const domain = u.hostname.replace('www.', '');
                    const cleanPath = u.pathname.length > 32 ? u.pathname.substring(0, 32) + '...' : u.pathname;
                    label = `<span class="source-domain">${domain}</span><span class="source-path">${cleanPath || '/'}</span>`;
                } catch(e) {
                    label = targetText;
                }
            }

            return `<a href="${targetHref}" target="_blank" rel="noopener noreferrer" class="source-link" title="${targetTitle || targetHref}"><i class="fa-solid fa-arrow-up-right-from-square text-[10px] opacity-80 mr-1 flex-shrink-0"></i><span>${label}</span></a>`;
        };

        marked.setOptions({
            renderer: customRenderer,
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true,
            gfm: true
        });

        // Preprocessor for Lightspeed responses
        function formatLightspeedMarkdown(content) {
            if (!content) return '';

            let formatted = content.replace(
                /(?:^|\n)(#{1,4}\s*)?(\*{1,2})?(Sources?|References?|Referensi|Rujukan):?(\*{1,2})?\s*(\n|$)/gi,
                '\n\n<div class="source-section-header"><i class="fa-solid fa-book-bookmark text-red-500 mr-2"></i><span>Sources & Red Hat Knowledgebase</span></div>\n\n'
            );

            formatted = formatted.replace(/(?<!\]\(|<|href="|src=")(https?:\/\/[^\s\)\<\>\'\"\]\`]+)/g, '[$1]($1)');

            return formatted;
        }

        // Category Tab Switching
        function switchCategory(cat) {
            currentCategory = cat;
            if (mainSidebar && mainSidebar.classList.contains('hidden')) {
                mainSidebar.classList.remove('hidden');
                localStorage.setItem('rh_sidebar_visible', 'true');
            }
            document.querySelectorAll('.category-tab').forEach(btn => {
                btn.classList.remove('active-tab');
                btn.classList.add('text-slate-400');
            });
            const activeBtn = document.getElementById(`tab-${cat}`);
            if (activeBtn) {
                activeBtn.classList.add('active-tab');
                activeBtn.classList.remove('text-slate-400');
            }
            renderPrompts(cat);
        }

        function renderPrompts(cat) {
            const prompts = CATEGORY_PROMPTS[cat] || [];
            promptContainer.innerHTML = prompts.map(p => `
                <div onclick="usePrompt('${cat}', '${p.prompt.replace(/'/g, "\\'")}')" 
                     class="p-2.5 bg-rh-card/70 hover:bg-rh-card rounded-lg border border-rh-border hover:border-red-500/50 cursor-pointer text-xs text-slate-200 transition group flex items-start">
                    <i class="fa-solid fa-chevron-right text-red-500 text-[10px] mt-1 mr-2 group-hover:translate-x-0.5 transition"></i>
                    <div>
                        <div class="font-semibold text-slate-100 group-hover:text-red-400 transition">${p.title}</div>
                        <div class="text-[11px] text-slate-400 line-clamp-1 mt-0.5">${p.prompt}</div>
                    </div>
                </div>
            `).join('');
        }

        // Sessions Management
        function loadSessions() {
            try {
                const stored = localStorage.getItem('rh_lightspeed_sessions');
                sessions = stored ? JSON.parse(stored) : [];
            } catch(e) {
                sessions = [];
            }

            if (sessions.length === 0) {
                createNewSession(false);
            } else {
                activeSessionId = sessions[0].id;
                renderSessionList();
                renderMessages();
            }
        }

        function saveSessions() {
            localStorage.setItem('rh_lightspeed_sessions', JSON.stringify(sessions));
            renderSessionList();
        }

        function createNewSession(save = true) {
            const newId = 'session_' + Date.now();
            const newSession = {
                id: newId,
                title: 'New Incident Investigation',
                messages: [],
                timestamp: Date.now()
            };
            sessions.unshift(newSession);
            activeSessionId = newId;
            if (save) saveSessions();
            renderSessionList();
            renderMessages();
            if (promptInput) promptInput.focus();
        }

        function switchSession(id) {
            activeSessionId = id;
            renderSessionList();
            renderMessages();
        }

        function clearAllSessions() {
            if (confirm('Hapus semua riwayat percakapan?')) {
                sessions = [];
                localStorage.removeItem('rh_lightspeed_sessions');
                createNewSession();
            }
        }

        function renderSessionList() {
            sessionList.innerHTML = sessions.map(s => `
                <div onclick="switchSession('${s.id}')" 
                     class="px-2.5 py-1.5 rounded text-xs cursor-pointer truncate transition flex items-center justify-between ${s.id === activeSessionId ? 'active-session text-white font-medium' : 'text-slate-400 hover:bg-rh-panel hover:text-slate-200'}">
                    <span class="truncate pr-2"><i class="fa-regular fa-message mr-1.5 text-[10px]"></i>${escapeHtml(s.title)}</span>
                    <button onclick="deleteSession(event, '${s.id}')" class="text-slate-500 hover:text-red-400 text-[10px]"><i class="fa-solid fa-xmark"></i></button>
                </div>
            `).join('');
        }

        function deleteSession(e, id) {
            e.stopPropagation();
            sessions = sessions.filter(s => s.id !== id);
            if (sessions.length === 0) {
                createNewSession();
            } else {
                activeSessionId = sessions[0].id;
                saveSessions();
                renderMessages();
            }
        }

        function renderMessages() {
            const currentSession = sessions.find(s => s.id === activeSessionId);
            chatMessages.innerHTML = '';

            if (!currentSession || currentSession.messages.length === 0) {
                chatMessages.appendChild(welcomeHub);
                welcomeHub.style.display = 'block';
                return;
            }

            welcomeHub.style.display = 'none';
            currentSession.messages.forEach(msg => appendMessageUI(msg.role, msg.content, false));
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function appendMessageUI(role, content, scroll = true) {
            if (welcomeHub.style.display !== 'none') {
                welcomeHub.style.display = 'none';
            }

            const msgDiv = document.createElement('div');
            const isUser = role === 'user';
            msgDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;

            msgDiv.innerHTML = `
                <div class="flex items-start space-x-3 max-w-[88%] sm:max-w-[80%] ${isUser ? 'flex-row-reverse space-x-reverse' : ''}">
                    <div class="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center text-xs text-white ${isUser ? 'bg-indigo-600' : 'bg-rh-red shadow-md shadow-red-950/40'}">
                        <i class="fa-solid ${isUser ? 'fa-user-tie' : 'fa-hat-cowboy'}"></i>
                    </div>
                    <div class="p-4 rounded-2xl ${isUser ? 'bg-rh-red text-white rounded-tr-none' : 'bg-rh-panel border border-rh-border text-slate-100 rounded-tl-none prose prose-invert prose-sm max-w-none shadow-md'}">
                        ${isUser ? escapeHtml(content) : marked.parse(formatLightspeedMarkdown(content))}
                    </div>
                </div>
            `;

            chatMessages.appendChild(msgDiv);
            if (!isUser) {
                addCopyButtons(msgDiv);
            }
            if (scroll) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            return msgDiv;
        }

        function addCopyButtons(container) {
            const preBlocks = container.querySelectorAll('pre');
            preBlocks.forEach(pre => {
                if (pre.querySelector('.copy-btn')) return;
                const btn = document.createElement('button');
                btn.className = 'copy-btn';
                btn.innerHTML = '<i class="fa-regular fa-copy mr-1"></i>Copy';
                btn.onclick = () => {
                    const code = pre.querySelector('code') ? pre.querySelector('code').innerText : pre.innerText;
                    navigator.clipboard.writeText(code);
                    btn.innerHTML = '<i class="fa-solid fa-check mr-1 text-emerald-400"></i>Copied!';
                    setTimeout(() => { btn.innerHTML = '<i class="fa-regular fa-copy mr-1"></i>Copy'; }, 2000);
                };
                pre.appendChild(btn);
            });
        }

        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
        }

        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(e);
            }
        }

        function usePrompt(category, promptText) {
            const catMap = {
                'cert': 'cert', 'certifications': 'cert', 'Certifications': 'cert',
                'rhel': 'rhel', 'RHEL': 'rhel',
                'ocp': 'ocp', 'OCP': 'ocp', 'openshift': 'ocp',
                'cloud': 'cloud', 'Cloud': 'cloud', 'rhoso': 'cloud', 'rhosp': 'cloud',
                'ansible': 'ansible', 'Ansible': 'ansible'
            };
            if (category && catMap[category]) {
                switchCategory(catMap[category]);
            }
            promptInput.value = promptText;
            autoResize(promptInput);
            promptInput.focus();
        }

        async function handleSend(e) {
            if (e) e.preventDefault();
            const text = promptInput.value.trim();
            if (!text) return;

            const session = sessions.find(s => s.id === activeSessionId);
            if (!session) return;

            if (session.messages.length === 0) {
                session.title = text.substring(0, 32) + (text.length > 32 ? '...' : '');
            }

            session.messages.push({ role: 'user', content: text });
            appendMessageUI('user', text);
            saveSessions();

            promptInput.value = '';
            autoResize(promptInput);
            promptInput.disabled = true;
            sendBtn.disabled = true;

            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'flex justify-start';
            loadingDiv.id = 'loadingIndicator';
            loadingDiv.innerHTML = `
                <div class="flex items-start space-x-3 max-w-[80%]">
                    <div class="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center text-xs text-white bg-rh-red">
                        <i class="fa-solid fa-hat-cowboy"></i>
                    </div>
                    <div class="p-3.5 rounded-2xl bg-rh-panel border border-rh-border text-slate-300 text-xs flex items-center space-x-2.5 shadow-md">
                        <i class="fa-solid fa-circle-notch fa-spin text-red-500"></i>
                        <span>Red Hat Lightspeed sedang menganalisis arsitektur dan sistem log...</span>
                    </div>
                </div>
            `;
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const response = await fetch('/v1/chat/completions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: 'rhel-lightspeed',
                        messages: session.messages,
                        stream: false
                    })
                });

                const data = await response.json();
                loadingDiv.remove();

                if (data.choices && data.choices.length > 0) {
                    const reply = data.choices[0].message.content;
                    session.messages.push({ role: 'assistant', content: reply });
                    appendMessageUI('assistant', reply);
                    saveSessions();
                } else if (data.error) {
                    appendMessageUI('assistant', `⚠️ **Lightspeed Error:** ${data.error}`);
                } else {
                    appendMessageUI('assistant', '⚠️ Respons tidak valid dari engine backend.');
                }
            } catch (err) {
                loadingDiv.remove();
                appendMessageUI('assistant', `❌ **Network / Backend Error:** ${err.message}`);
            } finally {
                promptInput.disabled = false;
                sendBtn.disabled = false;
                promptInput.focus();
            }
        }

        function toggleLogModal() {
            logModal.classList.toggle('hidden');
            if (!logModal.classList.contains('hidden')) {
                document.getElementById('rawLogInput').focus();
            }
        }

        function submitLogAnalysis() {
            const rawLog = document.getElementById('rawLogInput').value.trim();
            if (!rawLog) {
                alert('Silakan masukkan cuplikan log terlebih dahulu.');
                return;
            }
            toggleLogModal();
            document.getElementById('rawLogInput').value = '';
            
            const promptWithLog = `Berikut adalah cuplikan log sistem:\n\`\`\`\n${rawLog}\n\`\`\`\nTolong lakukan:\n1. Analisa Root Cause dari error di atas.\n2. Langkah perbaikan step-by-step berbasis CLI (RHEL/OCP).\n3. Perintah verifikasi pasca-remediasi.`;
            usePrompt('rhel', promptWithLog);
            handleSend();
        }

        function exportCurrentSession() {
            const session = sessions.find(s => s.id === activeSessionId);
            if (!session || session.messages.length === 0) {
                alert('Percakapan masih kosong.');
                return;
            }
            let md = `# ${session.title}\n\n*Dibuat oleh Red Hat Lightspeed AI Portal*\n*Tanggal: ${new Date(session.timestamp).toLocaleString()}*\n\n---\n\n`;
            session.messages.forEach(m => {
                md += `### ${m.role === 'user' ? '👤 SysAdmin' : '🎩 Red Hat Lightspeed'}\n\n${m.content}\n\n`;
            });
            const blob = new Blob([md], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${session.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
            a.click();
            URL.revokeObjectURL(url);
        }

        function escapeHtml(text) {
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
"""


class OpenAIBridgeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self._set_headers(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        self._set_headers(200, content_type="text/html; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        # OpenAI Models endpoint
        if self.path in ["/v1/models", "/models"]:
            models_response = {
                "object": "list",
                "data": [
                    {
                        "id": "rhel-lightspeed",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "redhat",
                        "permission": [],
                        "root": "rhel-lightspeed",
                        "parent": None,
                    }
                ]
            }
            body = json.dumps(models_response).encode("utf-8")
            self._set_headers(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # Health API
        elif self.path in ["/health", "/api/health", "/api/status"]:
            body = json.dumps({"status": "healthy", "service": "redhat-lightspeed-portal", "model": "rhel-lightspeed"}).encode("utf-8")
            self._set_headers(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # Web Portal UI
        elif self.path in ["/", "/chat", "/index.html"]:
            body = WEB_UI_HTML.encode("utf-8")
            self._set_headers(200, content_type="text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            body = json.dumps({"error": "Not Found"}).encode("utf-8")
            self._set_headers(404)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_POST(self):
        if self.path in ["/v1/chat/completions", "/chat/completions"]:
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            try:
                request_data = json.loads(post_body.decode("utf-8"))
            except Exception as e:
                body = json.dumps({"error": f"Invalid JSON format: {str(e)}"}).encode("utf-8")
                self._set_headers(400)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            # Save debug dump of request
            try:
                with open("/tmp/bridge_last_request.json", "w") as f:
                    json.dump(request_data, f, indent=2)
            except Exception:
                pass

            messages = request_data.get("messages", [])
            stream = request_data.get("stream", False)
            model = request_data.get("model", "rhel-lightspeed")
            tools = request_data.get("tools", [])

            prompt, is_tool_response, prev_cmd = self._extract_prompt_and_context(messages, tools)
            logger.info(f"Query for {model} (tools={len(tools)}, stream={stream}, is_tool_resp={is_tool_response}, prompt_len={len(prompt)})")

            try:
                reply_text = lightspeed.query(prompt)
            except Exception as e:
                logger.error(f"Error querying Lightspeed backend: {e}")
                body = json.dumps({"error": f"Lightspeed error: {str(e)}"}).encode("utf-8")
                self._set_headers(500)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            req_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
            created_ts = int(time.time())

            # Parse tool calls if tools are available (OpenCode Agent Mode)
            tool_command, leading_text = (None, reply_text)
            has_bash_tool = any(t.get("function", {}).get("name") == "bash" for t in tools if isinstance(t, dict))
            
            if has_bash_tool:
                cmd, lead_txt = self._parse_code_blocks(reply_text)
                # Avoid re-running the exact same command in a tool response turn
                if cmd and not (is_tool_response and prev_cmd and cmd.strip() == prev_cmd.strip()):
                    tool_command = cmd
                    leading_text = lead_txt

            if stream:
                self._set_headers(200, content_type="text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.end_headers()

                if tool_command:
                    call_id = f"call_{uuid.uuid4().hex[:12]}"
                    logger.info(f"Emitting tool_call for 'bash': {tool_command[:60]}...")

                    # Chunk 1: Explanation text (if any)
                    if leading_text:
                        c1 = {
                            "id": req_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": model,
                            "choices": [{
                                "index": 0,
                                "delta": {"role": "assistant", "content": leading_text + "\n\n"},
                                "finish_reason": None
                            }]
                        }
                        self.wfile.write(f"data: {json.dumps(c1)}\n\n".encode("utf-8"))
                        self.wfile.flush()

                    # Chunk 2: Tool call delta
                    c2 = {
                        "id": req_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "role": "assistant" if not leading_text else None,
                                "tool_calls": [{
                                    "index": 0,
                                    "id": call_id,
                                    "type": "function",
                                    "function": {
                                        "name": "bash",
                                        "arguments": json.dumps({"command": tool_command})
                                    }
                                }]
                            },
                            "finish_reason": None
                        }]
                    }
                    self.wfile.write(f"data: {json.dumps(c2)}\n\n".encode("utf-8"))
                    self.wfile.flush()

                    # Chunk 3: Finish reason tool_calls
                    c3 = {
                        "id": req_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "tool_calls"
                        }]
                    }
                    self.wfile.write(f"data: {json.dumps(c3)}\n\n".encode("utf-8"))
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                else:
                    # Regular text stream
                    chunk1 = {
                        "id": req_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant"},
                                "finish_reason": None
                            }
                        ]
                    }
                    self.wfile.write(f"data: {json.dumps(chunk1)}\n\n".encode("utf-8"))
                    self.wfile.flush()

                    words = reply_text.split(" ")
                    batch_size = 5
                    for i in range(0, len(words), batch_size):
                        sub_text = " ".join(words[i:i+batch_size])
                        if i + batch_size < len(words):
                            sub_text += " "
                        chunk_content = {
                            "id": req_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": sub_text},
                                    "finish_reason": None
                                }
                            ]
                        }
                        self.wfile.write(f"data: {json.dumps(chunk_content)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        time.sleep(0.005)

                    chunk_stop = {
                        "id": req_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop"
                            }
                        ]
                    }
                    self.wfile.write(f"data: {json.dumps(chunk_stop)}\n\n".encode("utf-8"))
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
            else:
                if tool_command:
                    call_id = f"call_{uuid.uuid4().hex[:12]}"
                    resp = {
                        "id": req_id,
                        "object": "chat.completion",
                        "created": created_ts,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": leading_text if leading_text else None,
                                    "tool_calls": [
                                        {
                                            "id": call_id,
                                            "type": "function",
                                            "function": {
                                                "name": "bash",
                                                "arguments": json.dumps({"command": tool_command})
                                            }
                                        }
                                    ]
                                },
                                "finish_reason": "tool_calls"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": len(prompt.split()),
                            "completion_tokens": len(reply_text.split()),
                            "total_tokens": len(prompt.split()) + len(reply_text.split())
                        }
                    }
                else:
                    resp = {
                        "id": req_id,
                        "object": "chat.completion",
                        "created": created_ts,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": reply_text
                                },
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": len(prompt.split()),
                            "completion_tokens": len(reply_text.split()),
                            "total_tokens": len(prompt.split()) + len(reply_text.split())
                        }
                    }
                body = json.dumps(resp).encode("utf-8")
                self._set_headers(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        else:
            body = json.dumps({"error": "Endpoint not found"}).encode("utf-8")
            self._set_headers(404)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def _extract_prompt_and_context(self, messages: List[Any], tools: List[Any]) -> Tuple[str, bool, Optional[str]]:
        if not messages:
            return ("", False, None)

        has_tools = bool(tools)
        tool_results = []
        user_messages = []
        last_tool_call_cmd = None
        is_tool_response = False

        for msg in messages:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = " ".join(text_parts)
            elif not isinstance(content, str):
                content = str(content)
            content = content.strip()

            if role == "user":
                user_messages.append(content)
            elif role == "assistant":
                t_calls = msg.get("tool_calls", [])
                for tc in t_calls:
                    fn = tc.get("function", {})
                    if fn.get("name") == "bash":
                        args_str = fn.get("arguments", "{}")
                        try:
                            args = json.loads(args_str)
                            last_tool_call_cmd = args.get("command")
                        except Exception:
                            pass
            elif role == "tool":
                is_tool_response = True
                tool_results.append(content)

        last_user_prompt = user_messages[-1] if user_messages else ""

        # Case 1: Title generator request
        if len(messages) <= 3 and any("title generator" in str(m.get("content", "")).lower() for m in messages):
            topic = last_user_prompt.replace("Generate a title for this conversation:", "").strip()
            prompt = f"Generate a brief 3-5 word title for this topic: {topic}"
            return (prompt, False, None)

        # Case 2: Response to tool execution (OpenCode completed a tool call and wants a summary)
        if is_tool_response and tool_results:
            last_output = tool_results[-1]
            if len(last_output) > 6000:
                last_output = last_output[:3000] + "\n... [truncated] ...\n" + last_output[-3000:]

            cmd_info = f"Command: {last_tool_call_cmd}\n" if last_tool_call_cmd else ""
            prompt = (
                f"The user requested: {last_user_prompt}\n"
                f"{cmd_info}"
                f"Command output from terminal:\n"
                f"{last_output}\n\n"
                f"Based on the command output above, answer the user request clearly and concisely in natural language.\n"
                f"If another command is strictly required to finish the task, provide it in a ```bash ... ``` block. Otherwise, provide your final response."
            )
            return (prompt, True, last_tool_call_cmd)

        # Case 3: Initial prompt with tools enabled (OpenCode agent mode)
        if has_tools:
            tool_names = [t.get("function", {}).get("name", "") for t in tools if isinstance(t, dict)]
            if "bash" in tool_names:
                prompt = (
                    f"Context: The user is working in a Linux terminal CLI (Red Hat Enterprise Linux). "
                    f"The client environment can execute bash commands on behalf of the user.\n"
                    f"User request: {last_user_prompt}\n\n"
                    f"If a bash command or action is needed to accomplish the task, provide the exact bash command inside a ```bash ... ``` code block.\n"
                    f"If multiple commands are needed, you can write them sequentially.\n"
                    f"If no command execution is needed (such as answering a concept or explaining something), answer the user question directly in natural language."
                )
                return (prompt, False, None)

        # Case 4: Standard chat mode (Web UI, cURL, etc.)
        extracted = []
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
            content = str(content).strip()
            if not content:
                continue
            if role == "user":
                extracted.append(content)
            elif role == "system" and len(content) < 500:
                extracted.append(f"[Context: {content}]")
            elif role == "assistant":
                extracted.append(f"Assistant: {content}")

        return ("\n\n".join(extracted), False, None)

    def _parse_code_blocks(self, reply_text: str) -> Tuple[Optional[str], str]:
        pattern = r'```(?:bash|sh|shell|zsh)\s*\n(.*?)\n```'
        matches = re.findall(pattern, reply_text, re.DOTALL)
        if not matches:
            generic_pattern = r'```\s*\n(.*?)\n```'
            generic_matches = re.findall(generic_pattern, reply_text, re.DOTALL)
            if generic_matches:
                first_candidate = generic_matches[0].strip()
                common_cmds = (
                    "ls", "cat", "echo", "mkdir", "rm", "cp", "mv", "touch", "git",
                    "dnf", "yum", "rpm", "systemctl", "journalctl", "uname", "df",
                    "free", "ps", "top", "find", "grep", "chmod", "chown", "curl",
                    "wget", "ip", "nmcli", "firewall-cmd", "sudo", "sed", "awk",
                    "tar", "gzip", "podman", "docker"
                )
                first_word = first_candidate.split()[0] if first_candidate.split() else ""
                if first_word in common_cmds or first_candidate.startswith("./") or first_candidate.startswith("/"):
                    matches = [first_candidate]

        if not matches:
            return (None, reply_text)

        command = matches[0].strip()
        code_start_idx = reply_text.find("```")
        leading_text = reply_text[:code_start_idx].strip() if code_start_idx != -1 else ""
        leading_text = re.sub(r'Sources:.*', '', leading_text, flags=re.DOTALL).strip()

        return (command, leading_text)

    def log_message(self, format, *args):
        logger.info("%s - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))


def run_server(host="0.0.0.0", port=80):
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, OpenAIBridgeHandler)
    logger.info(f"Red Hat Lightspeed AI Enterprise Portal & OpenCode Bridge running on http://{host}:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Portal & Bridge server...")
        httpd.server_close()


if __name__ == "__main__":
    port = 80
    host = "0.0.0.0"
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    if len(sys.argv) > 2:
        host = sys.argv[2]
    run_server(host=host, port=port)
