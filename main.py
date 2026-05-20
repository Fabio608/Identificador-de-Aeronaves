/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect, type FormEvent } from 'react';
import { 
  Settings, 
  Plane, 
  Plus, 
  Search, 
  Loader2,
  Calendar as CalendarIcon,
  Navigation,
  Wind,
  ArrowUpRight,
  X,
  LogOut,
  User as UserIcon,
  Download,
  FileArchive,
  RotateCcw
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from './lib/utils';
import { db, auth, handleFirestoreError, OperationType } from './lib/firebase';
import { 
  collection, 
  addDoc, 
  onSnapshot, 
  query, 
  where, 
  serverTimestamp, 
  doc, 
  setDoc 
} from 'firebase/firestore';
import { signInWithPopup, GoogleAuthProvider, onAuthStateChanged, signOut, type User } from 'firebase/auth';

interface Flight {
  id: string;
  date: string;
  flightNumber: string;
  registration: string;
  origin: string;
  destination: string;
  duration: string;
  std: string;
  atd: string;
  sta: string;
  status: string;
  altitude: number;
  speed: number;
}

interface Aircraft {
  id: string;
  registration: string;
  nickname: string;
}

export default function App() {
  const [registration, setRegistration] = useState('');
  const [date, setDate] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isAddingAircraft, setIsAddingAircraft] = useState(false);
  const [isConfiguringFR, setIsConfiguringFR] = useState(false);
  const [frApiKey, setFrApiKey] = useState('');
  const [isFrConfigured, setIsFrConfigured] = useState(false);
  const [newAircraftReg, setNewAircraftReg] = useState('');
  const [aircraftList, setAircraftList] = useState<Aircraft[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);

  useEffect(() => {
    const unsubscribeAuth = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setIsLoadingAuth(false);
    });
    return () => unsubscribeAuth();
  }, []);

  useEffect(() => {
    if (!user || !db) {
      setAircraftList([]);
      setIsFrConfigured(false);
      return;
    }

    // Config Listener
    const unsubscribeConfig = onSnapshot(doc(db, 'configs', user.uid), (snapshot) => {
      if (snapshot.exists()) {
        setIsFrConfigured(true);
        setFrApiKey(snapshot.data().flightradarApiKey || '');
      }
    });

    const q = query(collection(db, 'aircraft'), where('ownerId', '==', user.uid));
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const list = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Aircraft));
      setAircraftList(list);
    }, (err) => {
      console.error("Firestore error:", err);
      if (err.code !== 'permission-denied') {
        handleFirestoreError(err, OperationType.LIST, 'aircraft');
      }
    });

    return () => {
      unsubscribe();
      unsubscribeConfig();
    };
  }, [user]);

  const [isInterpreting, setIsInterpreting] = useState<string | null>(null);

  const handleDownloadTrace = async (id: string, type: 'kml' | 'kmz') => {
    setIsInterpreting(id);
    // Simulate trace reconstruction time
    await new Promise(r => setTimeout(r, 1200));
    window.open(`/api/flights/${id}/${type}`, '_blank');
    setIsInterpreting(null);
  };

  const handleLogin = async () => {
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (err) {
      console.error("Login error:", err);
      setError("Error al iniciar sesión con Google.");
    }
  };

  const handleLogout = () => signOut(auth);

  const handleSaveConfig = async (e: FormEvent) => {
    e.preventDefault();
    if (!user || !db) return;

    try {
      await setDoc(doc(db, 'configs', user.uid), {
        userId: user.uid,
        flightradarApiKey: frApiKey
      });
      setIsConfiguringFR(false);
      setIsFrConfigured(true);
    } catch (err) {
      handleFirestoreError(err, OperationType.WRITE, `configs/${user.uid}`);
    }
  };

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    const cleanReg = registration.trim();
    if (!cleanReg) return;

    setIsSearching(true);
    setError(null);
    try {
      const response = await fetch(`/api/flights/${encodeURIComponent(cleanReg)}`);
      const data = await response.json();
      setFlights(data.flights || []);
      if (!data.flights?.length) {
        setError('No se encontraron vuelos para esta aeronave.');
      }
    } catch (err) {
      setError('Error al buscar vuelos. Por favor, intente de nuevo.');
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleClearSearch = () => {
    setRegistration('');
    setDate('');
    setFlights([]);
    setError(null);
  };

  const handleQuickSelect = async (reg: string) => {
    const cleanReg = reg.trim();
    if (!cleanReg) return;
    setRegistration(cleanReg);
    setIsSearching(true);
    setError(null);
    try {
      const response = await fetch(`/api/flights/${encodeURIComponent(cleanReg)}`);
      const data = await response.json();
      setFlights(data.flights || []);
      if (!data.flights?.length) {
        setError('No se encontraron vuelos para esta aeronave.');
      }
    } catch (err) {
      setError('Error al buscar vuelos. Por favor, intente de nuevo.');
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAddAircraft = async (e: FormEvent) => {
    e.preventDefault();
    if (!newAircraftReg || !db || !user) return;

    try {
      await addDoc(collection(db, 'aircraft'), {
        registration: newAircraftReg.toUpperCase(),
        ownerId: user.uid,
        createdAt: serverTimestamp()
      });
      setNewAircraftReg('');
      setIsAddingAircraft(false);
    } catch (err) {
      handleFirestoreError(err, OperationType.CREATE, 'aircraft');
    }
  };

  return (
    <div className="min-h-screen bg-surface p-4 md:p-8 flex flex-col items-center">
      <div className="w-full max-w-2xl space-y-6">
        
        {/* Auth State / Sign In Header */}
        <div className="flex justify-between items-center px-2">
          {isLoadingAuth ? (
            <Loader2 className="w-5 h-5 animate-spin text-white/20" />
          ) : user ? (
            <div className="flex items-center gap-2">
              {user.photoURL ? (
                <img src={user.photoURL} alt="profile" className="w-8 h-8 rounded-full border border-white/10" referrerPolicy="no-referrer" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/60 font-bold text-xs uppercase tracking-tighter">
                  {user.displayName?.[0] || 'U'}
                </div>
              )}
              <div className="text-left">
                <p className="text-xs font-light text-white leading-none tracking-wide">{user.displayName}</p>
                <p className="text-[10px] text-white/30 leading-none mt-1 tracking-wider">{user.email}</p>
              </div>
            </div>
          ) : (
            <div className="text-[10px] uppercase tracking-[0.2em] text-white/30 flex items-center gap-2">
               <UserIcon className="w-3.5 h-3.5" /> Sign in for personal fleet
            </div>
          )}

          {user ? (
            <button 
              onClick={handleLogout}
              className="px-3 py-1.5 border border-white/10 rounded-lg text-[10px] uppercase tracking-widest text-white/60 hover:bg-white/5 flex items-center gap-1.5 transition-colors"
            >
              <LogOut className="w-3 h-3" /> Salir
            </button>
          ) : (
            <button 
              onClick={handleLogin}
              className="px-4 py-2 border border-brand/30 bg-brand/10 text-brand rounded-xl text-[10px] uppercase tracking-widest font-bold hover:bg-brand/20 transition-all active:scale-[0.98]"
            >
              Iniciar Sesión
            </button>
          )}
        </div>

        {/* Header / Config Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-card backdrop-blur-md rounded-xl p-4 border border-border-dim flex items-center justify-between"
          id="config-section"
        >
          <div className="flex items-center gap-3">
            <div className={cn(
              "p-2 rounded-lg border",
              isFrConfigured ? "bg-emerald-500/10 border-emerald-500/20" : "bg-white/5 border-white/5"
            )}>
              <Settings className={cn("w-4 h-4", isFrConfigured ? "text-emerald-400" : "text-white/40")} />
            </div>
            <div>
              <h2 className="text-xs uppercase tracking-[0.2em] font-medium text-white/80">
                {isFrConfigured ? "Flightradar24 Conectado" : "Configurar Flightradar24"}
              </h2>
              <p className="text-[10px] text-white/30 tracking-widest mt-0.5">
                {isFrConfigured ? "Sincronización activa con base de datos" : "Conecta tu cuenta para buscar vuelos reales"}
              </p>
            </div>
          </div>
          <button 
            onClick={() => setIsConfiguringFR(true)}
            className="p-1.5 hover:bg-white/5 rounded-full transition-colors group" 
            id="add-config-btn"
          >
            <Plus className="w-4 h-4 text-white/20 group-hover:text-white/40" />
          </button>
        </motion.div>

        {/* Fleet Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-card backdrop-blur-md rounded-xl p-5 border border-border-dim flex items-center justify-between"
          id="fleet-section"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 bg-brand/10 rounded-xl border border-brand/20">
              <Plane className="w-5 h-5 text-brand" />
            </div>
            <div>
              <h2 className="text-sm uppercase tracking-[0.2em] font-medium text-white/90">Mis Aeronaves</h2>
              <p className="text-[10px] text-white/30 tracking-widest mt-0.5">{aircraftList.length} aeronaves registradas</p>
            </div>
          </div>
          <button 
            onClick={() => setIsAddingAircraft(true)}
            className="p-1.5 hover:bg-white/5 rounded-full transition-colors group" 
            id="add-aircraft-btn"
          >
            <Plus className="w-5 h-5 text-white/20 group-hover:text-white/40" />
          </button>
        </motion.div>


        {/* Tracker Form Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-card backdrop-blur-xl p-10 border border-border-dim rounded-[32px] space-y-10"
          id="tracker-form-container"
        >
          <div className="space-y-2">
            <p className="text-brand text-[10px] uppercase tracking-[0.5em] font-semibold">Telemetry Engine</p>
            <div className="flex items-center gap-4">
              <Plane className="w-8 h-8 text-brand rotate-45" />
              <h1 className="text-5xl font-serif font-light tracking-tight text-white">Flight Tracker</h1>
            </div>
          </div>

          <form onSubmit={handleSearch} className="space-y-8">
            <div className="space-y-3">
              <label htmlFor="reg-input" className="text-[10px] uppercase tracking-[0.3em] font-medium text-white/30 ml-1">Aircraft Registration</label>
              <input
                id="reg-input"
                type="text"
                placeholder="e.g., N12345"
                value={registration}
                onChange={(e) => setRegistration(e.target.value)}
                className="w-full px-5 py-4 bg-white/[0.02] border border-white/10 rounded-2xl focus:ring-1 focus:ring-brand/50 focus:border-brand/40 focus:bg-white/[0.04] outline-none transition-all placeholder:text-white/10 text-white font-mono text-sm tracking-widest uppercase"
              />
            </div>

            <div className="space-y-3">
              <label htmlFor="date-input" className="text-[10px] uppercase tracking-[0.3em] font-medium text-white/30 ml-1">Flight Date</label>
              <div className="relative">
                <input
                  id="date-input"
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-5 py-4 bg-white/[0.02] border border-white/10 rounded-2xl focus:ring-1 focus:ring-brand/50 focus:border-brand/40 focus:bg-white/[0.04] outline-none transition-all text-white font-mono text-sm tracking-widest appearance-none"
                />
                <CalendarIcon className="w-4 h-4 text-white/20 absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <div className="flex gap-4">
              <button
                id="search-btn"
                type="submit"
                disabled={isSearching || !registration}
                className={cn(
                  "flex-1 py-5 border border-brand/20 bg-brand/5 text-brand rounded-2xl text-[11px] uppercase tracking-[0.4em] font-bold flex items-center justify-center gap-3 transition-all active:scale-[0.98]",
                  (isSearching || !registration) ? "opacity-30 cursor-not-allowed" : "hover:bg-brand hover:text-black hover:shadow-[0_0_20px_rgba(245,158,11,0.2)]"
                )}
              >
                {isSearching ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                Initialize Search
              </button>

              {(flights.length > 0 || registration || error) && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="px-6 py-5 border border-white/10 bg-white/5 text-white/60 rounded-2xl text-[11px] uppercase tracking-widest font-bold flex items-center justify-center gap-2 hover:bg-white/10 hover:text-white transition-all active:scale-[0.98]"
                  title="Limpiar búsqueda"
                >
                  <RotateCcw className="w-4 h-4" />
                  Limpiar
                </button>
              )}
            </div>
          </form>
        </motion.div>

        {/* Aircraft List (Quick Select) */}
        <AnimatePresence>
          {aircraftList.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="flex gap-2 overflow-x-auto pb-4 scrollbar-hide px-1"
              id="aircraft-quick-list"
            >
              {aircraftList.map((ac) => (
                <button
                  key={ac.id}
                  onClick={() => handleQuickSelect(ac.registration)}
                  className="whitespace-nowrap px-4 py-2 border border-white/5 bg-white/[0.02] rounded-full text-[9px] uppercase tracking-widest font-medium text-white/40 hover:text-white hover:border-white/20 hover:bg-white/5 transition-all shadow-sm"
                  title="Click para buscar"
                >
                  {ac.registration}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>


        {/* Results Section */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-red-950/20 text-red-400 p-5 rounded-2xl text-[10px] uppercase tracking-widest font-medium border border-red-900/30 text-center"
              id="error-message"
            >
              {error}
            </motion.div>
          )}

          {flights.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
              id="results-container"
            >
              <h3 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.4em] ml-1">Live Telemetry</h3>
              <div className="space-y-4">
                {flights.map((flight) => (
                  <div 
                    key={flight.id}
                    className="bg-card backdrop-blur-xl rounded-2xl p-6 border border-border-dim flex flex-wrap lg:flex-nowrap items-center gap-6 lg:gap-8 justify-between group hover:bg-white/[0.04] transition-all"
                    id={`flight-card-${flight.id}`}
                  >
                    {/* Date Column */}
                    <div className="w-24 shrink-0">
                      <p className="text-[11px] text-white/50 font-medium">{flight.date}</p>
                    </div>

                    {/* Route Section */}
                    <div className="flex items-center gap-6 min-w-[200px]">
                      <div className="text-left">
                        <span className="text-sm font-light text-white">{flight.origin.split('(')[0].trim()} </span>
                        <span className="text-[10px] text-brand font-medium">({flight.origin.match(/\((.*?)\)/)?.[1] || '???'})</span>
                      </div>
                      <div className="text-left">
                        <span className="text-sm font-light text-white">{flight.destination.split('(')[0].trim()} </span>
                        <span className="text-[10px] text-brand font-medium">({flight.destination.match(/\((.*?)\)/)?.[1] || '???'})</span>
                      </div>
                    </div>

                    {/* Flight Info Column */}
                    <div className="w-28 shrink-0 flex flex-col justify-center">
                      <span className="text-[11px] font-mono text-brand font-bold tracking-widest animate-pulse-subtle" title="Indicativo / Callsign">
                        {flight.flightNumber}
                      </span>
                      {flight.registration && flight.registration !== flight.flightNumber && (
                        <span className="text-[9px] text-white/40 tracking-wider mt-0.5" title="Matrícula / Registro">
                          Reg: <span className="font-mono text-white/60">{flight.registration}</span>
                        </span>
                      )}
                    </div>

                    {/* Duration Column */}
                    <div className="w-16 shrink-0">
                      <p className="text-[11px] text-white/40">{flight.duration}</p>
                    </div>

                    {/* Time Breakdown Column */}
                    <div className="flex gap-6 text-[11px] font-mono text-white/30 shrink-0">
                      <span>{flight.std}</span>
                      <span>{flight.atd}</span>
                      <span>{flight.sta}</span>
                    </div>

                    {/* Status Column */}
                    <div className="flex-1 flex items-center gap-3 border-l border-white/5 pl-6 min-w-[140px]">
                      <span className="text-[11px] font-medium text-emerald-400">
                        {flight.status}
                      </span>
                    </div>

                    {/* Action Column */}
                    <div className="shrink-0">
                      <div className="flex bg-white/[0.03] rounded-lg p-0.5 border border-white/5 items-center">
                        <button 
                          disabled={isInterpreting === flight.id}
                          onClick={() => handleDownloadTrace(flight.id, 'kml')}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[9px] uppercase tracking-widest font-bold text-white/40 hover:bg-brand/10 hover:text-brand transition-all disabled:opacity-50"
                        >
                          {isInterpreting === flight.id ? (
                            <motion.div 
                              animate={{ rotate: 360 }}
                              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            >
                              <Settings className="w-3 h-3" />
                            </motion.div>
                          ) : (
                            <Download className="w-3 h-3" />
                          )}
                          KML
                        </button>
                        <div className="w-[1px] bg-white/5 my-1 mx-0.5" />
                        <button 
                          disabled={isInterpreting === flight.id}
                          onClick={() => handleDownloadTrace(flight.id, 'kmz')}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[9px] uppercase tracking-widest font-bold text-white/40 hover:bg-brand/10 hover:text-brand transition-all disabled:opacity-50"
                        >
                          {isInterpreting === flight.id ? (
                            <span className="animate-pulse">...</span>
                          ) : (
                            <FileArchive className="w-3 h-3" />
                          )}
                          KMZ
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>


        <AddAircraftModal 
          isOpen={isAddingAircraft}
          onClose={() => setIsAddingAircraft(false)}
          onSubmit={handleAddAircraft}
          value={newAircraftReg}
          onChange={setNewAircraftReg}
        />

        <ConfigModal 
          isOpen={isConfiguringFR}
          onClose={() => setIsConfiguringFR(false)}
          onSubmit={handleSaveConfig}
          value={frApiKey}
          onChange={setFrApiKey}
        />
      </div>
    </div>
  );
}

function ConfigModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  value, 
  onChange 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  onSubmit: (e: FormEvent) => void;
  value: string;
  onChange: (val: string) => void;
}) {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-md"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="bg-surface w-full max-w-md rounded-[32px] p-10 border border-white/10 shadow-2xl relative z-10 space-y-8"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-2xl font-serif font-light text-white tracking-tight">API Configuration</h3>
              <button 
                onClick={onClose}
                className="p-2 hover:bg-white/5 rounded-full transition-colors text-white/20 hover:text-white/60"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={onSubmit} className="space-y-8">
              <div className="space-y-3">
                <label className="text-[10px] uppercase tracking-[0.3em] font-medium text-white/30 ml-1">Flightradar24 API Key</label>
                <input
                  autoFocus
                  type="password"
                  placeholder="Insert Key..."
                  value={value}
                  onChange={(e) => onChange(e.target.value)}
                  className="w-full px-5 py-4 bg-white/[0.02] border border-white/10 rounded-2xl focus:ring-1 focus:ring-brand/50 focus:border-brand/40 outline-none font-mono text-sm tracking-widest text-white placeholder:text-white/10"
                />
                <p className="text-[9px] text-white/20 leading-relaxed italic">
                  Tu llave se encripta y se guarda para permitir búsquedas históricas y descarga de trazas KML.
                </p>
              </div>

              <button
                type="submit"
                className="w-full py-5 border border-brand/20 bg-brand/5 text-brand rounded-2xl text-[11px] uppercase tracking-[0.4em] font-bold hover:bg-brand hover:text-black transition-all active:scale-[0.98]"
              >
                Garantizar Conexión
              </button>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

function AddAircraftModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  value, 
  onChange 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  onSubmit: (e: FormEvent) => void;
  value: string;
  onChange: (val: string) => void;
}) {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-md"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="bg-surface w-full max-w-md rounded-[32px] p-10 border border-white/10 shadow-2xl relative z-10 space-y-8"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-2xl font-serif font-light text-white tracking-tight">Registrar Aeronave</h3>
              <button 
                onClick={onClose}
                className="p-2 hover:bg-white/5 rounded-full transition-colors text-white/20 hover:text-white/60"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={onSubmit} className="space-y-8">
              <div className="space-y-3">
                <label className="text-[10px] uppercase tracking-[0.3em] font-medium text-white/30 ml-1">Matrícula (Registration)</label>
                <input
                  autoFocus
                  type="text"
                  placeholder="e.g., N12345"
                  value={value}
                  onChange={(e) => onChange(e.target.value)}
                  className="w-full px-5 py-4 bg-white/[0.02] border border-white/10 rounded-2xl focus:ring-1 focus:ring-brand/50 focus:border-brand/40 outline-none font-mono text-sm tracking-widest uppercase text-white placeholder:text-white/10"
                />
              </div>

              <button
                type="submit"
                className="w-full py-5 border border-brand/20 bg-brand/5 text-brand rounded-2xl text-[11px] uppercase tracking-[0.4em] font-bold hover:bg-brand hover:text-black transition-all active:scale-[0.98]"
              >
                Guardar Aeronave
              </button>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
