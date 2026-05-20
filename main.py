/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect, type FormEvent, useCallback } from 'react';
import { 
  Settings, Plane, Plus, Search, Loader2, Calendar as CalendarIcon, 
  LogOut, User as UserIcon, Download, FileArchive, RotateCcw, X 
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from './lib/utils';
import { db, auth, handleFirestoreError, OperationType } from './lib/firebase';
import { 
  collection, addDoc, onSnapshot, query, where, 
  serverTimestamp, doc, setDoc 
} from 'firebase/firestore';
import { signInWithPopup, GoogleAuthProvider, onAuthStateChanged, signOut, type User } from 'firebase/auth';

// --- Interfaces ---
interface Flight {
  id: string; date: string; flightNumber: string; registration: string;
  origin: string; destination: string; duration: string;
  std: string; atd: string; sta: string; status: string;
}

interface Aircraft { id: string; registration: string; }

// --- Main Component ---
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
  const [isInterpreting, setIsInterpreting] = useState<string | null>(null);

  // --- Lógica de Negocio Centralizada ---
  const performSearch = useCallback(async (reg: string) => {
    const cleanReg = reg.trim().toUpperCase();
    if (!cleanReg) return;

    setRegistration(cleanReg);
    setIsSearching(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/flights/${encodeURIComponent(cleanReg)}`);
      const data = await response.json();
      setFlights(data.flights || []);
      if (!data.flights?.length) setError('No se encontraron vuelos para esta aeronave.');
    } catch (err) {
      setError('Error al conectar con el servidor.');
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // --- Efectos (Auth & Data) ---
  useEffect(() => {
    const unsubscribeAuth = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setIsLoadingAuth(false);
    });
    return () => unsubscribeAuth();
  }, []);

  useEffect(() => {
    if (!user || !db) return;

    const unsubConfig = onSnapshot(doc(db, 'configs', user.uid), (snap) => {
      if (snap.exists()) {
        setIsFrConfigured(true);
        setFrApiKey(snap.data().flightradarApiKey || '');
      }
    });

    const q = query(collection(db, 'aircraft'), where('ownerId', '==', user.uid));
    const unsubAircraft = onSnapshot(q, (snap) => {
      setAircraftList(snap.docs.map(d => ({ id: d.id, ...d.data() } as Aircraft)));
    });

    return () => { unsubConfig(); unsubAircraft(); };
  }, [user]);

  // --- Handlers ---
  const handleDownloadTrace = async (id: string, type: 'kml' | 'kmz') => {
    setIsInterpreting(id);
    await new Promise(r => setTimeout(r, 1200));
    window.open(`/api/flights/${id}/${type}`, '_blank');
    setIsInterpreting(null);
  };

  const handleSaveConfig = async (e: FormEvent) => {
    e.preventDefault();
    if (!user || !db) return;
    try {
      await setDoc(doc(db, 'configs', user.uid), { userId: user.uid, flightradarApiKey: frApiKey });
      setIsConfiguringFR(false);
      setIsFrConfigured(true);
    } catch (err) { handleFirestoreError(err, OperationType.WRITE, 'configs'); }
  };

  const handleAddAircraft = async (e: FormEvent) => {
    e.preventDefault();
    if (!newAircraftReg || !db || !user) return;
    try {
      await addDoc(collection(db, 'aircraft'), { 
        registration: newAircraftReg.toUpperCase(), ownerId: user.uid, createdAt: serverTimestamp() 
      });
      setNewAircraftReg('');
      setIsAddingAircraft(false);
    } catch (err) { handleFirestoreError(err, OperationType.CREATE, 'aircraft'); }
  };

  return (
    <div className="min-h-screen bg-surface p-4 md:p-8 flex flex-col items-center">
      <div className="w-full max-w-2xl space-y-6">
        
        {/* Auth Section */}
        <div className="flex justify-between items-center px-2">
          {isLoadingAuth ? <Loader2 className="animate-spin text-white/20" /> : (
            <div className="flex items-center gap-2">
              {user ? (
                <>
                  <img src={user.photoURL || ''} className="w-8 h-8 rounded-full" alt="avatar" />
                  <div className="text-xs text-white">{user.displayName}</div>
                </>
              ) : <div className="text-[10px] text-white/30 uppercase tracking-[0.2em]">Sign in for fleet</div>}
            </div>
          )}
          {user ? (
            <button onClick={() => signOut(auth)} className="text-[10px] text-white/60 uppercase tracking-widest border border-white/10 px-3 py-1.5 rounded-lg">Salir</button>
          ) : (
            <button onClick={() => signInWithPopup(auth, new GoogleAuthProvider())} className="text-[10px] text-brand border border-brand/30 bg-brand/10 px-4 py-2 rounded-xl">Iniciar Sesión</button>
          )}
        </div>

        {/* ... (Aquí iría el resto del JSX: Config, Fleet, Form, etc.) ... */}
        {/* Nota: Mantené la estructura anterior para ConfigModal y AddAircraftModal igual que en tu código original. */}
      </div>
    </div>
  );
}

// (Incluir aquí ConfigModal y AddAircraftModal definidos en tu código original)
