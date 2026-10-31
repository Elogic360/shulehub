import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Accordion } from '../components/ui/Accordion';
import {
  Building,
  GraduationCap,
  Users,
  MessageSquare,
  FileSpreadsheet,
  Receipt,
  Smartphone,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Menu,
  X,
  Calendar,
  Layers,
  Award,
  Clock,
  Sparkles,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Send,
  Eye,
  Lock,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { user, t } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [previewTab, setPreviewTab] = useState<'dashboard' | 'exams' | 'sms' | 'fees'>('dashboard');

  const scrollTo = (id: string) => {
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const faqItems = [
    {
      id: 'faq-1',
      question: 'What is ShuleConnect?',
      answer:
        'ShuleConnect is a specialized education communication and parent-engagement SaaS engineered specifically for primary and secondary schools in Tanzania. It centralizes student records, class teacher workflows, multi-subject examination releases, school fee reminders, and parent announcements through reliable Bulk SMS and interactive USSD.',
    },
    {
      id: 'faq-2',
      question: 'Which schools can use ShuleConnect?',
      answer:
        'ShuleConnect natively supports both Tanzanian private primary schools (Standard 1 to 6/7) and secondary schools (Form 1 to 4/6). Schools with combined primary and secondary branches can easily configure academic levels, class streams (e.g. Standard 3A, Form 2B), and subject teachers.',
    },
    {
      id: 'faq-3',
      question: 'Do parents need smartphones or internet connections?',
      answer:
        'No. Parents do not need smartphones or data plans to stay informed. ShuleConnect dispatches announcements, attendance updates, and fee reminders directly to standard mobile phones via telecom SMS. Parents can also dial the interactive USSD code (*384*55#) on any basic feature phone to view grades and fee balances.',
    },
    {
      id: 'faq-4',
      question: 'Can teachers send individual messages or only bulk announcements?',
      answer:
        'Class teachers have full flexibility. They can broadcast whole-class notices, send targeted messages to selected guardians, or communicate individually with a specific child’s parent, while maintaining full message delivery tracking and administrative oversight.',
    },
    {
      id: 'faq-5',
      question: 'How do examination results uploads work?',
      answer:
        'Schools upload results directly using standardized Excel (.xlsx) or CSV spreadsheets. The platform validates student admission numbers, calculates NECTA standard grades (A, B, C, D, F) and subject points, enforces an administrative approval stage, and issues confidential notifications to parents.',
    },
    {
      id: 'faq-6',
      question: 'How are sensitive student examination marks protected?',
      answer:
        'In strict compliance with the Tanzania Personal Data Protection Act (PDPA 2022), raw examination marks are never broadcast over unencrypted, public bulk SMS. Instead, parents receive a notification containing a private, tokenized link or a 6-digit cryptographic OTP challenge via USSD to view their child’s confidential report.',
    },
    {
      id: 'faq-7',
      question: 'Can ShuleConnect send automated fee reminders?',
      answer:
        'Yes. The system tracks fee schedules, invoices, and payment receipts. Background automation (powered by Celery Beat) monitors outstanding balances and dispatches polite, scheduled reminders to guardians as payment deadlines approach, with financial reconciliation discrepancy detection.',
    },
    {
      id: 'faq-8',
      question: 'How does school registration and onboarding work?',
      answer:
        'To maintain strict tenant privacy and institution verification, school onboarding is managed via authorized administrative invitation links issued by platform Super Administrators. Once an invitation is created, school owners configure their academic levels, assign staff, and start managing communications immediately.',
    },
    {
      id: 'faq-9',
      question: 'Does ShuleConnect support USSD access for parents?',
      answer:
        'Yes. Parents dial the provisioned USSD shortcode (*384*55#). If a parent has children across different schools, the system deterministically routes them to their chosen school, requires a 6-digit cryptographic SMS OTP before revealing sensitive academic marks, and displays verified fee balances.',
    },
    {
      id: 'faq-10',
      question: 'How can our school get started today?',
      answer:
        'Click the "Get Started" or "Register Your School" button to request an onboarding link from the ShuleConnect administration team. Our team verifies your school registration and provides direct access to start enrolling classes within minutes.',
    },
  ];

  return (
    <div className="min-h-screen bg-brand-bgSurface text-brand-textPrimary font-sans antialiased selection:bg-brand-teal/20 selection:text-brand-navy">
      {/* ================= SECTION 1 — NAVIGATION HEADER ================= */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200/80 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-brand-navy flex items-center justify-center text-brand-teal font-black text-2xl shadow-sm group-hover:scale-105 transition-transform">
              S
            </div>
            <div>
              <span className="font-black text-xl tracking-tight text-brand-navy">
                Shule<span className="text-brand-teal">Connect</span>
              </span>
              <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest -mt-1">
                Tanzania Education SaaS
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-600">
            <button onClick={() => scrollTo('features')} className="hover:text-brand-navy transition">
              Features
            </button>
            <button onClick={() => scrollTo('how-it-works')} className="hover:text-brand-navy transition">
              How It Works
            </button>
            <button onClick={() => scrollTo('solutions')} className="hover:text-brand-navy transition">
              Solutions
            </button>
            <button onClick={() => scrollTo('preview')} className="hover:text-brand-navy transition">
              Product Preview
            </button>
            <button onClick={() => scrollTo('pricing')} className="hover:text-brand-navy transition">
              Pricing
            </button>
            <button onClick={() => scrollTo('faq')} className="hover:text-brand-navy transition">
              FAQ
            </button>
          </nav>

          {/* Header Action CTAs */}
          <div className="hidden sm:flex items-center gap-3">
            {user ? (
              <Button
                variant="primary"
                size="md"
                onClick={() => {
                  if (user.is_superadmin) navigate('/admin');
                  else if (user.roles?.includes('CLASS_TEACHER')) navigate('/teacher');
                  else if (user.roles?.includes('PARENT')) navigate('/parent');
                  else navigate('/owner');
                }}
                rightIcon={<ArrowRight className="w-4 h-4 text-brand-teal" />}
              >
                Go to Dashboard
              </Button>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="md">
                    Sign In
                  </Button>
                </Link>
                <Link to="/register-school">
                  <Button variant="primary" size="md" rightIcon={<ArrowRight className="w-4 h-4 text-brand-teal" />}>
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Hamburger Toggle */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-b border-slate-200 px-4 pt-2 pb-6 space-y-3 animate-in slide-in-from-top-2 duration-150">
            <button
              onClick={() => scrollTo('features')}
              className="block w-full text-left py-2 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              Features
            </button>
            <button
              onClick={() => scrollTo('how-it-works')}
              className="block w-full text-left py-2 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              How It Works
            </button>
            <button
              onClick={() => scrollTo('solutions')}
              className="block w-full text-left py-2 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              Solutions
            </button>
            <button
              onClick={() => scrollTo('preview')}
              className="block w-full text-left py-2 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              Product Preview
            </button>
            <button
              onClick={() => scrollTo('pricing')}
              className="block w-full text-left py-2 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              Pricing
            </button>
            <button
              onClick={() => scrollTo('faq')}
              className="block w-full text-left py-2 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 rounded-lg"
            >
              FAQ
            </button>
            <div className="pt-3 border-t border-slate-100 flex flex-col gap-2">
              <Link to="/login" className="w-full">
                <Button variant="outline" size="md" className="w-full">
                  Sign In
                </Button>
              </Link>
              <Link to="/register-school" className="w-full">
                <Button variant="primary" size="md" className="w-full">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* ================= SECTION 2 — HERO ================= */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-32 bg-gradient-to-b from-white via-slate-50 to-brand-bgSurface">
        {/* Subtle decorative background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-brand-teal/5 blur-3xl rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center max-w-4xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-50 border border-teal-200 text-brand-teal text-xs font-bold uppercase tracking-wider shadow-sm">
              <Sparkles className="w-4 h-4 text-brand-teal" />
              <span>Built for Tanzanian Primary & Secondary Schools</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-brand-navy tracking-tight leading-[1.15]">
              Connecting Schools, Teachers, and Parents —{' '}
              <span className="text-brand-teal underline decoration-brand-teal/30 decoration-wavy underline-offset-8">
                Effortlessly.
              </span>
            </h1>

            <p className="text-lg sm:text-xl text-brand-textSecondary max-w-3xl mx-auto leading-relaxed">
              ShuleConnect helps primary and secondary schools in Tanzania manage student information, share
              examination updates, send announcements, and communicate fee reminders through one simple platform
              powered by SMS and USSD.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <Link to="/register-school" className="w-full sm:w-auto">
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full sm:w-auto shadow-lg hover:shadow-xl"
                  rightIcon={<ArrowRight className="w-5 h-5 text-brand-teal" />}
                >
                  Get Started
                </Button>
              </Link>
              <button onClick={() => scrollTo('features')} className="w-full sm:w-auto">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  Explore Features
                </Button>
              </button>
            </div>

            {/* Trust highlights */}
            <div className="pt-8 flex flex-wrap items-center justify-center gap-6 sm:gap-12 text-xs font-semibold text-slate-500">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Africa's Talking SMS & USSD</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Tanzania PDPA 2022 Compliant</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>NECTA Grading Standards</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>PostgreSQL 18 Multi-Tenant RLS</span>
              </div>
            </div>
          </div>

          {/* Hero Realistic Application Interface Preview */}
          <div className="mt-14 max-w-5xl mx-auto rounded-2xl bg-white p-2 sm:p-4 shadow-2xl border border-slate-200/90 overflow-hidden">
            <div className="bg-slate-900 rounded-xl overflow-hidden border border-slate-800">
              {/* Mock Window Header */}
              <div className="h-11 bg-slate-950 px-4 flex items-center justify-between border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="ml-3 text-xs font-mono text-slate-400 font-medium hidden sm:inline">
                    https://shuleconnect.co.tz/owner/dashboard
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="teal" size="sm">
                    Live Demo View
                  </Badge>
                </div>
              </div>

              {/* Realistic Dashboard Preview Canvas */}
              <div className="p-6 bg-slate-900 text-white space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
                  <div>
                    <span className="text-xs font-bold text-brand-teal uppercase tracking-wider block">
                      St. Jude Academy (Ilala, Dar es Salaam)
                    </span>
                    <h2 className="text-xl font-black text-white mt-0.5">
                      Term 1 Academic & Communication Overview
                    </h2>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-3 py-1 rounded bg-slate-800 text-slate-300 font-medium">
                      Academic Year 2026
                    </span>
                    <span className="px-3 py-1 rounded bg-emerald-950/70 border border-emerald-500/30 text-emerald-400 font-bold">
                      SMS Balance: 8,420 TZS
                    </span>
                  </div>
                </div>

                {/* 4 Metric Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/60">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                      Enrolled Students
                    </span>
                    <div className="text-2xl font-black text-white mt-1">486</div>
                    <span className="text-[11px] text-emerald-400 mt-0.5 block">100% with Guardians</span>
                  </div>
                  <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/60">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                      Class Teachers
                    </span>
                    <div className="text-2xl font-black text-white mt-1">14</div>
                    <span className="text-[11px] text-slate-400 mt-0.5 block">Std 1 to Std 6 Streams</span>
                  </div>
                  <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/60">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                      SMS Dispatched
                    </span>
                    <div className="text-2xl font-black text-brand-teal mt-1">3,240</div>
                    <span className="text-[11px] text-emerald-400 mt-0.5 block">99.4% Delivered Rate</span>
                  </div>
                  <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/60">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                      Fee Collection Rate
                    </span>
                    <div className="text-2xl font-black text-indigo-400 mt-1">84.2%</div>
                    <span className="text-[11px] text-slate-400 mt-0.5 block">Auto Reminders Active</span>
                  </div>
                </div>

                {/* Sample Activity Snapshot */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 space-y-3">
                    <div className="flex items-center justify-between text-xs font-bold text-slate-300">
                      <span>Recent Class Announcement</span>
                      <span className="text-emerald-400">Delivered</span>
                    </div>
                    <p className="text-xs text-slate-400 bg-slate-900/80 p-3 rounded-lg border border-slate-800 leading-relaxed font-mono">
                      "Dear Parent, Standard 4 Mid-Term Results are released. Dial *384*55# or view confidential card:
                      shuleconnect.co.tz/r/x91k"
                    </p>
                  </div>
                  <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 space-y-2">
                    <div className="flex items-center justify-between text-xs font-bold text-slate-300">
                      <span>NECTA Assessment Integration</span>
                      <span className="text-brand-teal font-mono">FTNA 2025</span>
                    </div>
                    <div className="space-y-1.5 text-xs text-slate-400">
                      <div className="flex justify-between py-1 border-b border-slate-700/40">
                        <span>Center S.0101 Registered Candidates:</span>
                        <span className="text-white font-bold">128</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span>Auto-Matched to Enrolled Students:</span>
                        <span className="text-emerald-400 font-bold">128 (100%)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= SECTION 3 — BENEFITS ================= */}
      <section id="benefits" className="py-20 bg-white border-y border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
            <Badge variant="teal">Proven Operational Value</Badge>
            <h2 className="text-3xl sm:text-4xl font-black text-brand-navy tracking-tight">
              One Platform for School Communication
            </h2>
            <p className="text-base text-slate-600 leading-relaxed">
              Eliminate lost paper notices, missed fee payment deadlines, and stressful report card distribution drives
              with a platform crafted for local educational infrastructure.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="hover:border-brand-teal/40 transition">
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-brand-teal mb-4">
                  <Smartphone className="w-6 h-6" />
                </div>
                <CardTitle>Reach Parents Instantly</CardTitle>
                <CardDescription>
                  Send whole-school notices or targeted classroom alerts through Africa's Talking SMS gateway with
                  strict GSM 7-bit and Unicode cost optimization.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="hover:border-brand-teal/40 transition">
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-brand-actionBlue mb-4">
                  <GraduationCap className="w-6 h-6" />
                </div>
                <CardTitle>Manage Classes with Confidence</CardTitle>
                <CardDescription>
                  Empower class teachers as frontline administrators of their specific class streams with strict
                  boundary isolation that protects other classrooms.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="hover:border-brand-teal/40 transition">
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 mb-4">
                  <Award className="w-6 h-6" />
                </div>
                <CardTitle>Share Examination Updates</CardTitle>
                <CardDescription>
                  Import spreadsheet marks, automatically calculate NECTA division points, and distribute confidential,
                  PDPA-compliant report cards securely.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="hover:border-brand-teal/40 transition">
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 mb-4">
                  <Receipt className="w-6 h-6" />
                </div>
                <CardTitle>Simplify Fee Reminders</CardTitle>
                <CardDescription>
                  Track student invoice ledgers, compare external snapshot balances, apply authorized waivers, and
                  automate polite parent fee reminders.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="hover:border-brand-teal/40 transition">
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 mb-4">
                  <Users className="w-6 h-6" />
                </div>
                <CardTitle>Keep Guardians Informed</CardTitle>
                <CardDescription>
                  Connect primary and secondary guardians to their children, maintaining complete contact history audits
                  and multi-school USSD routing.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="hover:border-brand-teal/40 transition">
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-300 flex items-center justify-center text-brand-navy mb-4">
                  <TrendingUp className="w-6 h-6" />
                </div>
                <CardTitle>Track Communication Activity</CardTitle>
                <CardDescription>
                  Monitor real-time delivery reports (DLR) distinguishing initial telco acceptance from physical handset
                  delivery confirmation.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* ================= SECTION 4 — CORE FEATURES ================= */}
      <section id="features" className="py-20 bg-brand-bgSurface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <Badge variant="primary">Comprehensive Capabilities</Badge>
            <h2 className="text-3xl sm:text-4xl font-black text-brand-navy tracking-tight">
              Engineered for Modern School Operations
            </h2>
            <p className="text-base text-slate-600">
              Six synchronized operational modules that eliminate administrative bottlenecks.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="w-10 h-10 rounded-lg bg-brand-navy text-brand-teal flex items-center justify-center font-bold">
                1
              </div>
              <h3 className="text-lg font-bold text-brand-navy">School & Class Management</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Configure Standard 1–6 (Primary) or Form 1–4 (Secondary) academic structures, class streams, teacher
                assignments, and permanent student profiles with USSD access IDs.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-2 border-t border-slate-100">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Multi-stream support (Stream A, B, C)
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Class teacher role authorization
                </li>
              </ul>
            </div>

            {/* Feature 2 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="w-10 h-10 rounded-lg bg-brand-navy text-brand-teal flex items-center justify-center font-bold">
                2
              </div>
              <h3 className="text-lg font-bold text-brand-navy">Parent Communication Engine</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Dispatch personalized SMS broadcasts using smart templates (e.g., student name, balance due). Choose
                between whole-school, class-wide, or individual guardian modes.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-2 border-t border-slate-100">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Real-time character & segment counter
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Carrier delivery report webhooks
                </li>
              </ul>
            </div>

            {/* Feature 3 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="w-10 h-10 rounded-lg bg-brand-navy text-brand-teal flex items-center justify-center font-bold">
                3
              </div>
              <h3 className="text-lg font-bold text-brand-navy">Examination Results & NECTA</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Upload grade sheets, validate score limits, and publish authorized reports. Ingest official NECTA FTNA/CSEE
                national results with automatic candidate index matching.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-2 border-t border-slate-100">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Confidential tokenized parent links
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> NECTA candidate review queue
                </li>
              </ul>
            </div>

            {/* Feature 4 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="w-10 h-10 rounded-lg bg-brand-navy text-brand-teal flex items-center justify-center font-bold">
                4
              </div>
              <h3 className="text-lg font-bold text-brand-navy">Fee Management & Reconciliation</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Create term fee schedules, track payments across bank slips and mobile money, detect ledger discrepancies
                against snapshot imports, and issue audit-tracked waivers.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-2 border-t border-slate-100">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Automatic balance calculations
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Scheduled fee reminder rules
                </li>
              </ul>
            </div>

            {/* Feature 5 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="w-10 h-10 rounded-lg bg-brand-navy text-brand-teal flex items-center justify-center font-bold">
                5
              </div>
              <h3 className="text-lg font-bold text-brand-navy">Interactive USSD Handset Gateway</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Enable parents on basic feature phones to query student performance and fee balances by dialing
                *384*55#, protected by a 6-digit cryptographic SMS OTP challenge.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-2 border-t border-slate-100">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Multi-school routing menu
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> 3-attempt brute-force protection
                </li>
              </ul>
            </div>

            {/* Feature 6 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="w-10 h-10 rounded-lg bg-brand-navy text-brand-teal flex items-center justify-center font-bold">
                6
              </div>
              <h3 className="text-lg font-bold text-brand-navy">Parent-Teacher Meetings</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Schedule academic conferences, send direct RSVP notices to parents via SMS, track attendee confirmations,
                and improve parent engagement with zero phone calls.
              </p>
              <ul className="text-xs text-slate-500 space-y-1.5 pt-2 border-t border-slate-100">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Real-time confirmation tracking
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Automated event reminders
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ================= SECTION 5 — HOW IT WORKS ================= */}
      <section id="how-it-works" className="py-20 bg-white border-y border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
            <Badge variant="teal">Fast Onboarding</Badge>
            <h2 className="text-3xl sm:text-4xl font-black text-brand-navy tracking-tight">
              Four Steps to Streamlined Communication
            </h2>
            <p className="text-base text-slate-600">
              Get your institution up and running without costly hardware or complex software installations.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
            {/* Step 1 */}
            <div className="space-y-4 text-center sm:text-left">
              <div className="w-12 h-12 rounded-xl bg-brand-navy text-white flex items-center justify-center text-lg font-black mx-auto sm:mx-0 shadow-md">
                01
              </div>
              <h3 className="text-base font-bold text-brand-navy">Register Your School</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Activate your authorized school account, choose Primary, Secondary, or Combined level, and establish
                your academic year.
              </p>
            </div>

            {/* Step 2 */}
            <div className="space-y-4 text-center sm:text-left">
              <div className="w-12 h-12 rounded-xl bg-brand-teal text-white flex items-center justify-center text-lg font-black mx-auto sm:mx-0 shadow-md">
                02
              </div>
              <h3 className="text-base font-bold text-brand-navy">Create Classes & Teachers</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Configure classroom streams (e.g. Standard 1A, Form 2B) and assign class teachers with dedicated
                operational access.
              </p>
            </div>

            {/* Step 3 */}
            <div className="space-y-4 text-center sm:text-left">
              <div className="w-12 h-12 rounded-xl bg-brand-actionBlue text-white flex items-center justify-center text-lg font-black mx-auto sm:mx-0 shadow-md">
                03
              </div>
              <h3 className="text-base font-bold text-brand-navy">Add Students & Guardians</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Bulk upload students and parent phone numbers via the Excel Import Center, generating unique USSD
                access IDs automatically.
              </p>
            </div>

            {/* Step 4 */}
            <div className="space-y-4 text-center sm:text-left">
              <div className="w-12 h-12 rounded-xl bg-emerald-600 text-white flex items-center justify-center text-lg font-black mx-auto sm:mx-0 shadow-md">
                04
              </div>
              <h3 className="text-base font-bold text-brand-navy">Communicate & Share</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Send bulk notices, publish confidential examination cards, and trigger automated fee reminders through
                SMS and USSD.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ================= SECTION 6 — SOLUTIONS ================= */}
      <section id="solutions" className="py-20 bg-brand-bgSurface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <Badge variant="primary">Tailored Architecture</Badge>
            <h2 className="text-3xl sm:text-4xl font-black text-brand-navy tracking-tight">
              Solutions Designed for Every Educational Role
            </h2>
            <p className="text-base text-slate-600">
              Each user group receives a purpose-built workspace tailored to their exact daily responsibilities.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="hover:shadow-lg transition">
              <CardHeader>
                <div className="w-10 h-10 rounded-lg bg-teal-50 text-brand-teal flex items-center justify-center font-bold mb-3">
                  <Building className="w-5 h-5" />
                </div>
                <CardTitle>For Primary & Secondary Schools</CardTitle>
                <CardDescription>
                  Supports the full Tanzanian curriculum lifecycle. Adaptable academic levels from Standard 1 to Form 4,
                  multi-branch campuses, and official NECTA national exam synchronization.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <Link to="/register-school" className="text-xs font-bold text-brand-teal hover:underline flex items-center gap-1">
                  <span>Explore School Solutions</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition">
              <CardHeader>
                <div className="w-10 h-10 rounded-lg bg-blue-50 text-brand-actionBlue flex items-center justify-center font-bold mb-3">
                  <Users className="w-5 h-5" />
                </div>
                <CardTitle>For Class Teachers</CardTitle>
                <CardDescription>
                  A clean, isolated workspace for daily classroom tasks. Upload exam marks, broadcast attendance or
                  homework announcements, and view SMS delivery statuses without administrative complexity.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <Link to="/login" className="text-xs font-bold text-brand-actionBlue hover:underline flex items-center gap-1">
                  <span>Sign In as Teacher</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition">
              <CardHeader>
                <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold mb-3">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <CardTitle>For Parents & Guardians</CardTitle>
                <CardDescription>
                  Real-time visibility into your child's education. Receive instant SMS alerts, review confidential grade
                  reports via protected web links, or check balances by dialing *384*55# on any phone.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <Link to="/login" className="text-xs font-bold text-emerald-600 hover:underline flex items-center gap-1">
                  <span>Access Parent Portal</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* ================= SECTION 7 — PRODUCT PREVIEW ================= */}
      <section id="preview" className="py-20 bg-white border-y border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <Badge variant="teal">Interactive Demonstration</Badge>
            <h2 className="text-3xl sm:text-4xl font-black text-brand-navy tracking-tight">
              Experience the Real ShuleConnect Interface
            </h2>
            <p className="text-base text-slate-600">
              Click through the tabs below to explore our role-based dashboards and communication workflows.
            </p>
          </div>

          {/* Interactive Preview Tabs */}
          <div className="flex flex-wrap items-center justify-center gap-2 max-w-2xl mx-auto bg-slate-100 p-1.5 rounded-xl border border-slate-200">
            <button
              onClick={() => setPreviewTab('dashboard')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                previewTab === 'dashboard'
                  ? 'bg-brand-navy text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              School Dashboard
            </button>
            <button
              onClick={() => setPreviewTab('exams')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                previewTab === 'exams'
                  ? 'bg-brand-navy text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Examination Matrix
            </button>
            <button
              onClick={() => setPreviewTab('sms')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                previewTab === 'sms'
                  ? 'bg-brand-navy text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Communication Outbox
            </button>
            <button
              onClick={() => setPreviewTab('fees')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                previewTab === 'fees'
                  ? 'bg-brand-navy text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Fee Reconciliation
            </button>
          </div>

          {/* Tab Display Area */}
          <div className="max-w-4xl mx-auto bg-slate-50 rounded-2xl border border-slate-200 p-6 shadow-sm">
            {previewTab === 'dashboard' && (
              <div className="space-y-4 animate-in fade-in duration-200">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <span className="text-xs font-bold text-brand-navy uppercase tracking-wider">
                    School Owner & Administrator Overview
                  </span>
                  <Badge variant="success">Active Term 1</Badge>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-white p-4 rounded-xl border border-slate-200">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Total Students</span>
                    <div className="text-xl font-bold text-brand-navy">512</div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-slate-200">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Class Groups</span>
                    <div className="text-xl font-bold text-brand-navy">12</div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-slate-200">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Delivery Health</span>
                    <div className="text-xl font-bold text-emerald-600">99.8%</div>
                  </div>
                </div>
                <p className="text-xs text-slate-500 italic">
                  * Live data connects directly to authorized tenant instances without exposing cross-school records.
                </p>
              </div>
            )}

            {previewTab === 'exams' && (
              <div className="space-y-4 animate-in fade-in duration-200">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <span className="text-xs font-bold text-brand-navy uppercase tracking-wider">
                    Mid-Term Examination Results — Standard 4A
                  </span>
                  <Badge variant="teal">NECTA Standards</Badge>
                </div>
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden text-xs">
                  <div className="grid grid-cols-4 bg-slate-100 font-bold p-2.5 text-slate-700">
                    <span>Admission No</span>
                    <span>Student Name</span>
                    <span>Average %</span>
                    <span>Grade & Division</span>
                  </div>
                  <div className="grid grid-cols-4 p-2.5 border-b border-slate-100 text-slate-700">
                    <span className="font-mono">STD4/001</span>
                    <span className="font-medium">Amina Bakari</span>
                    <span className="text-emerald-700 font-bold">86.4%</span>
                    <span>Grade A (Division I)</span>
                  </div>
                  <div className="grid grid-cols-4 p-2.5 border-b border-slate-100 text-slate-700">
                    <span className="font-mono">STD4/002</span>
                    <span className="font-medium">Juma Rashid</span>
                    <span className="text-emerald-700 font-bold">78.0%</span>
                    <span>Grade A (Division I)</span>
                  </div>
                </div>
              </div>
            )}

            {previewTab === 'sms' && (
              <div className="space-y-4 animate-in fade-in duration-200">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <span className="text-xs font-bold text-brand-navy uppercase tracking-wider">
                    Bulk Campaign Dispatch Monitor
                  </span>
                  <Badge variant="blue">Gateway Connected</Badge>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-700">Campaign: General Assembly Announcement</span>
                    <span className="text-emerald-600 font-bold">486 / 486 Sent</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div className="bg-brand-teal h-full w-full" />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500">
                    <span>Encoding: GSM-7 (1 Segment per recipient)</span>
                    <span>Gateway: Africa's Talking v2</span>
                  </div>
                </div>
              </div>
            )}

            {previewTab === 'fees' && (
              <div className="space-y-4 animate-in fade-in duration-200">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <span className="text-xs font-bold text-brand-navy uppercase tracking-wider">
                    Financial Ledger Discrepancy & Waiver Engine
                  </span>
                  <Badge variant="warning">Audit Logged</Badge>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 text-xs space-y-2">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Invoiced Total:</span>
                    <span className="font-bold text-slate-800">TZS 500,000</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Payments Recorded:</span>
                    <span className="font-bold text-emerald-600">TZS 350,000</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Outstanding Balance:</span>
                    <span className="font-bold text-amber-700">TZS 150,000</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ================= SECTION 8 — SMS & USSD EXPERIENCE ================= */}
      <section className="py-20 bg-brand-navy text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <span className="text-xs font-bold text-brand-teal uppercase tracking-widest block">
              Telecommunications Pipeline
            </span>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
              Reliable Delivery Across Every Network
            </h2>
            <p className="text-sm sm:text-base text-slate-300">
              How ShuleConnect guarantees communication reaching parents on Vodacom, Airtel, Tigo, Halotel, and TTCL.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
            <div className="bg-slate-800/80 p-5 rounded-xl border border-slate-700 text-center space-y-2">
              <span className="text-xs font-bold text-brand-teal">Step 1</span>
              <h4 className="text-sm font-bold text-white">Teacher Action</h4>
              <p className="text-xs text-slate-400">Class teacher drafts announcement or uploads marks.</p>
            </div>
            <div className="hidden md:flex justify-center text-brand-teal">
              <ArrowRight className="w-5 h-5" />
            </div>
            <div className="bg-slate-800/80 p-5 rounded-xl border border-slate-700 text-center space-y-2">
              <span className="text-xs font-bold text-brand-teal">Step 2</span>
              <h4 className="text-sm font-bold text-white">Validation & Queue</h4>
              <p className="text-xs text-slate-400">E.164 normalization, GSM-7 segmentation, Celery worker queue.</p>
            </div>
            <div className="hidden md:flex justify-center text-brand-teal">
              <ArrowRight className="w-5 h-5" />
            </div>
            <div className="bg-slate-800/80 p-5 rounded-xl border border-slate-700 text-center space-y-2">
              <span className="text-xs font-bold text-brand-teal">Step 3</span>
              <h4 className="text-sm font-bold text-white">Africa's Talking & DLR</h4>
              <p className="text-xs text-slate-400">Delivered to handset; carrier delivery report reconciled.</p>
            </div>
          </div>

          {/* USSD Dialing Demonstration Card */}
          <div className="max-w-xl mx-auto bg-slate-950 p-6 rounded-2xl border border-slate-800 text-center space-y-4 shadow-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 text-xs font-mono text-brand-teal">
              <Smartphone className="w-4 h-4" />
              <span>USSD Shortcode: *384*55#</span>
            </div>
            <h3 className="text-base font-bold text-white">Feature Phone Access for All Guardians</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Parents dial *384*55# on any standard phone. If multiple children attend different institutions, the
              menu provides intuitive school routing. Sensitive exam reports require entering a 6-digit cryptographic
              SMS OTP before scores are displayed.
            </p>
          </div>
        </div>
      </section>

      {/* ================= SECTION 9 — PRIVACY & SECURITY ================= */}
      <section className="py-20 bg-white border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
            <Badge variant="success">Tanzania PDPA 2022</Badge>
            <h2 className="text-3xl sm:text-4xl font-black text-brand-navy tracking-tight">
              Enterprise Privacy & Security Architecture
            </h2>
            <p className="text-base text-slate-600">
              Student records and school communications are protected by rigorous database kernel and application-level controls.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-brand-navy">PostgreSQL Row-Level Security</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Tenant isolation is enforced natively at the PostgreSQL 18 kernel level (`tenant_isolation_policy`).
                No school can ever access or leak another school's student or financial data.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-100 text-brand-teal flex items-center justify-center font-bold">
                <Lock className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-brand-navy">Tokenized Result Notifications</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Exam marks are never exposed across open unencrypted SMS. Parents receive secure, tokenized verification
                links or 6-digit OTP prompts to access their child's confidential performance.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 text-brand-actionBlue flex items-center justify-center font-bold">
                <Clock className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-brand-navy">Auditable Contact Journals</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Changes to guardian telephone numbers are immutably logged in `guardian_contact_history`, immediately
                invalidating prior active USSD sessions to prevent unauthorized phone transfer takeovers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ================= SECTION 10 — PRICING ================= */}
      <section id="pricing" className="py-20 bg-brand-bgSurface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <Badge variant="primary">Simple & Transparent</Badge>
            <h2 className="text-3xl sm:text-4xl font-black text-brand-navy tracking-tight">
              Flexible Plans for Schools of Every Size
            </h2>
            <p className="text-base text-slate-600">
              Clear institutional tiers with included SMS credits and unlimited teacher accounts.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Starter Plan */}
            <Card className="hover:border-slate-300 transition flex flex-col">
              <CardHeader>
                <CardTitle>Starter School</CardTitle>
                <CardDescription>Ideal for single-stream primary or nursery campuses.</CardDescription>
                <div className="pt-4">
                  <span className="text-3xl font-black text-brand-navy">TZS 150,000</span>
                  <span className="text-xs text-slate-400 font-medium"> / term</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-slate-600 flex-1">
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> Up to 250 Enrolled Students
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> Unlimited Teacher Logins
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> Examination Marks Center
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> Standard SMS Notification Rail
                </li>
              </CardContent>
              <div className="p-6 pt-0">
                <Link to="/register-school">
                  <Button variant="outline" size="md" className="w-full">
                    Request Onboarding
                  </Button>
                </Link>
              </div>
            </Card>

            {/* Growth Plan (Featured) */}
            <Card className="border-2 border-brand-teal shadow-xl relative flex flex-col">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <Badge variant="teal" size="sm">
                  Most Popular in Tanzania
                </Badge>
              </div>
              <CardHeader>
                <CardTitle>Growth Campus</CardTitle>
                <CardDescription>For growing multi-stream primary and secondary schools.</CardDescription>
                <div className="pt-4">
                  <span className="text-3xl font-black text-brand-navy">TZS 350,000</span>
                  <span className="text-xs text-slate-400 font-medium"> / term</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-slate-600 flex-1">
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-teal shrink-0" /> Up to 800 Enrolled Students
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-teal shrink-0" /> Multi-Stream Class Groups (A, B, C)
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-teal shrink-0" /> Excel Spreadsheet Import Center
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-teal shrink-0" /> Fee Balance Ledger & Reminders
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-brand-teal shrink-0" /> Interactive USSD Parent Access
                </li>
              </CardContent>
              <div className="p-6 pt-0">
                <Link to="/register-school">
                  <Button variant="primary" size="md" className="w-full">
                    Get Started with Growth
                  </Button>
                </Link>
              </div>
            </Card>

            {/* Enterprise Plan */}
            <Card className="hover:border-slate-300 transition flex flex-col">
              <CardHeader>
                <CardTitle>Enterprise & Combined</CardTitle>
                <CardDescription>For large schools, boarding academies, and multi-school groups.</CardDescription>
                <div className="pt-4">
                  <span className="text-3xl font-black text-brand-navy">TZS 650,000</span>
                  <span className="text-xs text-slate-400 font-medium"> / term</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-slate-600 flex-1">
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> Unlimited Enrolled Students
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> Primary & Secondary Combined
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> NECTA National Assessment Sync
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> Custom Alphanumeric Sender ID
                </li>
                <li className="flex items-center gap-2 list-none">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> Priority Technical Support
                </li>
              </CardContent>
              <div className="p-6 pt-0">
                <Link to="/register-school">
                  <Button variant="outline" size="md" className="w-full">
                    Contact Enterprise Sales
                  </Button>
                </Link>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* ================= SECTION 11 — FAQ ================= */}
      <section id="faq" className="py-20 bg-white border-t border-slate-200/80">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center space-y-4">
            <Badge variant="teal">Frequently Asked Questions</Badge>
            <h2 className="text-3xl sm:text-4xl font-black text-brand-navy tracking-tight">
              Everything You Need to Know About ShuleConnect
            </h2>
            <p className="text-base text-slate-600">
              Clear, transparent answers about how ShuleConnect operates in Tanzanian schools.
            </p>
          </div>

          <Accordion items={faqItems} />
        </div>
      </section>

      {/* ================= SECTION 12 — FINAL CALL TO ACTION ================= */}
      <section id="get-started" className="py-20 bg-gradient-to-br from-brand-navy via-slate-900 to-slate-950 text-white relative overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6 relative z-10">
          <Badge variant="teal">Join Forward-Thinking Schools</Badge>
          <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
            Bring Your School and Parents Closer Together.
          </h2>
          <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Start building stronger communication between your school, teachers, and families with ShuleConnect.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link to="/register-school" className="w-full sm:w-auto">
              <Button
                variant="teal"
                size="lg"
                className="w-full sm:w-auto shadow-xl"
                rightIcon={<ArrowRight className="w-5 h-5 text-white" />}
              >
                Register Your School
              </Button>
            </Link>
            <Link to="/login" className="w-full sm:w-auto">
              <Button variant="outline" size="lg" className="w-full sm:w-auto text-white border-slate-700 hover:bg-slate-800">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ================= SECTION 13 — FOOTER ================= */}
      <footer className="bg-slate-950 text-slate-400 py-16 border-t border-slate-800 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8 pb-12 border-b border-slate-800">
            {/* Brand column */}
            <div className="col-span-2 space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-navy flex items-center justify-center text-brand-teal font-black text-xl">
                  S
                </div>
                <span className="font-bold text-lg text-white">
                  Shule<span className="text-brand-teal">Connect</span>
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed max-w-sm">
                Production-oriented education communication and parent engagement SaaS for private primary and
                secondary schools in Tanzania.
              </p>
              <div className="text-[11px] text-slate-500 font-mono">
                Operating System: Linux / PostgreSQL 18 / Valkey Native
              </div>
            </div>

            {/* Navigation 1: Platform */}
            <div className="space-y-3">
              <span className="font-bold text-white uppercase tracking-wider block text-xs">Platform</span>
              <ul className="space-y-2">
                <li><button onClick={() => scrollTo('features')} className="hover:text-white transition">Core Features</button></li>
                <li><button onClick={() => scrollTo('how-it-works')} className="hover:text-white transition">How It Works</button></li>
                <li><button onClick={() => scrollTo('preview')} className="hover:text-white transition">Live Preview</button></li>
                <li><button onClick={() => scrollTo('pricing')} className="hover:text-white transition">Pricing Plans</button></li>
              </ul>
            </div>

            {/* Navigation 2: Solutions */}
            <div className="space-y-3">
              <span className="font-bold text-white uppercase tracking-wider block text-xs">Solutions</span>
              <ul className="space-y-2">
                <li><button onClick={() => scrollTo('solutions')} className="hover:text-white transition">Primary Schools</button></li>
                <li><button onClick={() => scrollTo('solutions')} className="hover:text-white transition">Secondary Schools</button></li>
                <li><button onClick={() => scrollTo('solutions')} className="hover:text-white transition">Class Teachers</button></li>
                <li><button onClick={() => scrollTo('solutions')} className="hover:text-white transition">Parents & Guardians</button></li>
              </ul>
            </div>

            {/* Navigation 3: Regulatory & Access */}
            <div className="space-y-3">
              <span className="font-bold text-white uppercase tracking-wider block text-xs">Access</span>
              <ul className="space-y-2">
                <li><Link to="/login" className="hover:text-white transition">Staff Sign In</Link></li>
                <li><Link to="/register-school" className="hover:text-white transition">School Registration</Link></li>
                <li><Link to="/ussd-simulator" className="hover:text-white transition">USSD *384*55#</Link></li>
                <li><button onClick={() => scrollTo('faq')} className="hover:text-white transition">Help & FAQ</button></li>
              </ul>
            </div>
          </div>

          <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-slate-500 text-[11px]">
            <div>
              © 2026 ShuleConnect Technologies Ltd. All rights reserved. Tanzania PDPA 2022 compliant.
            </div>
            <div className="flex items-center gap-6">
              <span>Privacy Policy</span>
              <span>Terms of Service</span>
              <span>Dar es Salaam, Tanzania</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
