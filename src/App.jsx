import { useEffect, useState } from "react";
import { onValue, ref } from "firebase/database";
import { db, FIREBASE_PATH } from "./firebase";

const GREEN = "#059669";
const RED = "#DC2626";
const OFFLINE_AFTER_MS = 10_000; // sem dados há mais de 10s => Offline

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

function formatTime(ts) {
  if (!ts) return "--:--:--";
  return new Date(ts).toLocaleTimeString("pt-BR", { hour12: false });
}

export default function App() {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(true);
  const [now, setNow] = useState(Date.now());

  // Escuta em tempo real o Firebase (sem refresh)
  useEffect(() => {
    const unsubscribe = onValue(
      ref(db, FIREBASE_PATH),
      (snap) => {
        setData(snap.val());
        setConnected(true);
      },
      () => setConnected(false)
    );
    return unsubscribe;
  }, []);

  // Relógio interno para detetar quando o script deixa de enviar dados
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const lucroBrl = data?.lucro_brl ?? 0;
  const isGreen = data ? lucroBrl >= 0 : true;
  const bg = isGreen ? GREEN : RED;
  const isOnline =
    connected && !!data?.timestamp && now - data.timestamp < OFFLINE_AFTER_MS;

  // Cor da barra do navegador do telemóvel acompanha o fundo
  useEffect(() => {
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", bg);
  }, [bg]);

  return (
    <main
      className="flex min-h-full flex-col text-white transition-colors duration-500"
      style={{ backgroundColor: bg, minHeight: "100dvh" }}
    >
      {/* Centro: valor em destaque */}
      <section className="flex flex-1 flex-col items-center justify-center px-4 text-center">
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.3em] opacity-80">
          {!data ? "Aguardando dados..." : isGreen ? "Lucro flutuante" : "Prejuízo flutuante"}
        </p>
        <h1 className="text-6xl font-extrabold tabular-nums leading-none sm:text-8xl">
          {data ? brl.format(lucroBrl) : "—"}
        </h1>
      </section>

      {/* Rodapé */}
      <footer
        className="grid grid-cols-2 gap-x-4 gap-y-3 bg-black/20 px-5 pt-4 text-sm"
        style={{ paddingBottom: "calc(1rem + env(safe-area-inset-bottom))" }}
      >
        <Info label="Ordens abertas" value={data?.posicoes_abertas ?? "—"} />
        <Info label="Lucro USD" value={data ? usd.format(data.lucro_usd) : "—"} />
        <Info label="Última atualização" value={formatTime(data?.timestamp)} />
        <div>
          <p className="text-xs uppercase tracking-wider opacity-70">Status</p>
          <p className="mt-0.5 flex items-center gap-2 text-base font-semibold">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${
                isOnline ? "animate-pulse bg-white" : "bg-black/50"
              }`}
            />
            {isOnline ? "Online" : "Offline"}
          </p>
        </div>
      </footer>
    </main>
  );
}

function Info({ label, value }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wider opacity-70">{label}</p>
      <p className="mt-0.5 text-base font-semibold tabular-nums">{value}</p>
    </div>
  );
}
