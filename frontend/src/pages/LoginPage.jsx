import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Eye,
  EyeOff,
  Lock,
  User,
  ShieldCheck,
  ToggleRight,
  Loader2
} from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const API_BASE = 'http://localhost:8000';

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
  localStorage.setItem("tax_token", data.token);
  localStorage.setItem("isAuthenticated", "true");
  localStorage.setItem("user", data.username || username);
  localStorage.setItem("role", data.role || "admin");

  navigate("/dashboard");
} else {
        setError(data.detail || 'Authentication failed. Please check credentials.');
      }
    } catch (err) {
      setError('Unable to reach authentication server.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterAdmin = async () => {
    setRegistering(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/auth/register-admin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        setError('');
        alert('Admin registered successfully. Now signing in...');
        document.querySelector('form')?.requestSubmit();
      } else {
        setError(data.detail || 'Admin registration failed.');
      }
    } catch (err) {
      setError('Unable to reach authentication server.');
    } finally {
      setRegistering(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#F1F5F9] p-4 font-sans text-slate-800">
      <div className="relative w-full max-w-sm bg-white border border-slate-200 p-8 rounded-2xl shadow-xl">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-slate-950 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <ShieldCheck className="w-9 h-9 text-white" />
          </div>

          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Tax Intel AI
          </h1>

          <p className="text-[10px] font-bold text-blue-600 uppercase tracking-[0.25em]">
            Government of Pakistan
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 text-xs rounded-lg text-center font-bold">
            {error}
          </div>
        )}

        <form className="space-y-5" onSubmit={handleLogin}>
          <div className="space-y-1.5 group">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Admin Username
            </label>

            <div className="relative">
              <User className="absolute left-3 top-3 w-4 h-4 text-slate-400" />

              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-9 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                placeholder="admin"
              />
            </div>
          </div>

          <div className="space-y-1.5 group">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              System Password
            </label>

            <div className="relative">
              <Lock className="absolute left-3 top-3 w-4 h-4 text-slate-400" />

              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-9 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                placeholder="••••••••"
              />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-slate-400 hover:text-slate-700"
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between py-3 px-4 bg-slate-50 rounded-lg border border-slate-100">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />

              <div>
                <p className="text-xs font-bold text-slate-900">
                  Admin Access
                </p>
                <p className="text-[9px] text-slate-500">
                  Protected Backend APIs
                </p>
              </div>
            </div>

            <ToggleRight className="w-8 h-8 text-emerald-600 cursor-pointer" />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-slate-950 hover:bg-blue-600 text-white font-bold py-3.5 rounded-lg text-sm flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="animate-spin w-4 h-4" />
            ) : (
              'Sign In Access →'
            )}
          </button>

          <button
            type="button"
            disabled={registering}
            onClick={handleRegisterAdmin}
            className="w-full bg-white border border-slate-200 hover:bg-slate-50 text-slate-900 font-bold py-3 rounded-lg text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {registering ? (
              <Loader2 className="animate-spin w-4 h-4" />
            ) : (
              'Register First Admin'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}