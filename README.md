# Dashboard de Monitorização MT5 em Tempo Real

Backend Python (no PC com o MetaTrader 5) → Firebase Realtime Database → Dashboard web (React + Tailwind) na Vercel.

```
mt5-dashboard/
├── script_mt5.py        # Backend: lê lucro flutuante e envia ao Firebase (1s)
├── requirements.txt     # Dependências Python
├── .env.example         # Modelo de configuração (copie para .env)
├── package.json         # Dependências do frontend
├── index.html
├── vite.config.js / tailwind.config.js / postcss.config.js
└── src/
    ├── main.jsx
    ├── App.jsx          # Dashboard
    ├── firebase.js      # Conexão Firebase
    └── index.css
```

> **Importante:** a biblioteca `MetaTrader5` só funciona em **Windows**, com o terminal MT5 aberto e logado.

---

## 1. Criar o Firebase (uma única vez)

1. Em https://console.firebase.google.com crie um projeto.
2. **Build → Realtime Database → Create database** (modo bloqueado).
3. Em **Rules**, cole e publique:

```json
{
  "rules": {
    "monitor": {
      ".read": true,
      ".write": false
    }
  }
}
```

   Qualquer pessoa com o link poderá **ler** `monitor`; só o seu script (com o *database secret*) consegue **escrever**.

4. **Project settings → Service accounts → Database secrets** → copie o segredo para `FIREBASE_DB_SECRET`.
   (Se este menu não aparecer, use a alternativa abaixo.)
5. **Project settings → General → Your apps → Web (`</>`)** → copie `apiKey`, `authDomain`, `databaseURL`, `projectId` e `appId`.

> **Alternativa sem secret:** nas regras, troque `".write": false` por `".write": true`. Funciona, mas qualquer pessoa que descubra a URL do banco poderá escrever dados falsos. Use apenas para testes.

## 2. Configurar o `.env`

```bash
cp .env.example .env        # Windows (cmd): copy .env.example .env
```

Preencha os valores. O mesmo `.env` serve para o Python e para o frontend em desenvolvimento local.

## 3. Rodar o script Python (PC com MT5)

Abra o MetaTrader 5, faça login e deixe-o aberto. No terminal da pasta do projeto:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python script_mt5.py
```

Deve aparecer algo como `GREEN | R$ 10.15 | US$ 1.85 | 1 pos.` a cada segundo.

Dados enviados para `monitor` no Firebase:

```json
{
  "lucro_brl": 10.15,
  "lucro_usd": 1.85,
  "posicoes_abertas": 1,
  "status": "GREEN",
  "timestamp": 1760000000000
}
```

- **Câmbio:** por padrão usa a API AwesomeAPI (atualizada a cada 60s). Para taxa fixa, defina `USD_BRL_FIXED=5.40` no `.env`.
- **Lucro** = soma de `profit + swap` das posições abertas (na moeda da conta; o script avisa se não for USD).

## 4. Rodar o dashboard localmente

```bash
npm install
npm run dev
```

Abra o endereço mostrado (também acessível pelo telemóvel na mesma rede Wi-Fi).

## 5. Subir para o GitHub

```bash
git init
git add .
git commit -m "MT5 dashboard"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/mt5-dashboard.git
git push -u origin main
```

O `.gitignore` já impede o envio do `.env`.

## 6. Deploy automático na Vercel

1. Em https://vercel.com → **Add New → Project** → importe o repositório.
2. A Vercel detecta **Vite** sozinha (Build: `npm run build`, Output: `dist`).
3. Em **Environment Variables**, cadastre as 6 variáveis `VITE_FIREBASE_*` do `.env`.
4. Clique em **Deploy**.

A cada `git push` na `main`, a Vercel faz novo deploy automaticamente. Abra o URL gerado no telemóvel (e adicione ao ecrã inicial, se quiser).

## 7. Usar em outro computador (Empresa/Casa)

```bash
git clone https://github.com/SEU_USUARIO/mt5-dashboard.git
cd mt5-dashboard
copy .env.example .env     # preencha com os mesmos valores
pip install -r requirements.txt
python script_mt5.py
```

> Rode o script em **apenas um PC por vez**, senão os dois escrevem no mesmo nó e os valores se alternam.

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| `Não foi possível conectar ao MT5` | Terminal fechado/sem login ou Python/MT5 de arquiteturas diferentes (use ambos 64 bits) |
| `401 Permission denied` no Python | `FIREBASE_DB_SECRET` vazio/errado com `.write: false` |
| Dashboard fica "Offline" | Script parado ou sem internet (sem dados há mais de 10s) |
| Dashboard em branco | Variáveis `VITE_*` faltando na Vercel (faça Redeploy após cadastrá-las) |
