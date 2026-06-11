import React from 'react';

// Mapa ESQUEMÁTICO da FIR Oceânica do Sal (GVSC) — sub-projeto D.
// Não é cartograficamente preciso (não temos as coordenadas do AIP): é um
// diagrama ilustrativo da posição estratégica do FIR no Atlântico, com Cabo
// Verde e os FIRs/continentes vizinhos por direção. Desenho próprio (sem
// licenciamento de terceiros). Escala de brancos para contraste sobre o fundo
// escuro (grafite) — regra frontend-design: nunca Carmesim sobre fundo escuro.

const W = 'rgba(255,255,255,';

export const FirMap = () => (
  <figure className="animate-fade-up">
    <svg
      viewBox="0 0 480 400"
      className="w-full max-w-md mx-auto h-auto"
      role="img"
      aria-labelledby="firmap-title firmap-desc"
    >
      <title id="firmap-title">FIR Oceânica do Sal (GVSC)</title>
      <desc id="firmap-desc">
        Esquema da posição da FIR Oceânica do Sal no Atlântico, com Cabo Verde ao
        centro e os FIRs vizinhos (Canárias, Dakar, Recife) e rotas transatlânticas.
      </desc>

      {/* Graticula subtil (leitura de oceano/globo) */}
      <g stroke={`${W}0.06)`} strokeWidth="1" fill="none">
        <path d="M60 60 Q240 30 420 60" />
        <path d="M40 140 Q240 110 440 140" />
        <path d="M40 260 Q240 290 440 260" />
        <path d="M60 340 Q240 370 420 340" />
        <path d="M120 40 Q150 200 120 360" />
        <path d="M240 30 Q240 200 240 370" />
        <path d="M360 40 Q330 200 360 360" />
      </g>

      {/* Área do FIR Oceânica do Sal (esquemática) */}
      <path
        d="M150 95 L360 110 Q400 140 392 210 L375 300 Q360 330 300 332 L170 325 Q110 318 100 250 L96 165 Q100 120 150 95 Z"
        fill={`${W}0.05)`}
        stroke={`${W}0.45)`}
        strokeWidth="1.5"
        strokeDasharray="6 5"
      />
      <text x="240" y="128" textAnchor="middle" fill={`${W}0.85)`} fontSize="13" fontWeight="700" letterSpacing="0.5">
        FIR OCEÂNICA DO SAL
      </text>
      <text x="240" y="146" textAnchor="middle" fill={`${W}0.5)`} fontSize="11" letterSpacing="2">
        GVSC · ~1,3 M km²
      </text>

      {/* Rotas transatlânticas */}
      <g stroke={`${W}0.3)`} strokeWidth="1.25" fill="none" strokeLinecap="round">
        <path d="M120 300 Q240 150 380 150" />
        <path d="M380 250 Q240 240 130 130" />
      </g>
      {/* Pequenos aviões nas pontas das rotas */}
      <g fill={`${W}0.7)`}>
        <path d="M380 150 l-9 -3 l2 3 l-2 3 z" transform="rotate(-18 380 150)" />
        <path d="M130 130 l-9 -3 l2 3 l-2 3 z" transform="rotate(150 130 130)" />
      </g>

      {/* Cabo Verde — cluster de ilhas ao centro */}
      <g fill={`${W}0.9)`}>
        <circle cx="232" cy="205" r="3.2" />
        <circle cx="246" cy="201" r="2.6" />
        <circle cx="258" cy="208" r="2.6" />
        <circle cx="226" cy="218" r="2.4" />
        <circle cx="240" cy="222" r="2.4" />
        <circle cx="254" cy="222" r="2.4" />
        <circle cx="220" cy="230" r="2.2" />
      </g>
      {/* Sal (sede do ACC) destacado */}
      <circle cx="258" cy="208" r="5.5" fill="none" stroke={`${W}0.8)`} strokeWidth="1.3" />
      <text x="270" y="200" fill={`${W}0.85)`} fontSize="10.5" fontWeight="600">Sal · ACC</text>
      <text x="220" y="248" textAnchor="middle" fill={`${W}0.7)`} fontSize="11" fontWeight="600">Cabo Verde</text>

      {/* FIRs / continentes vizinhos por direção */}
      <g fill={`${W}0.45)`} fontSize="10">
        <text x="408" y="78" textAnchor="end">Canárias FIR ↗</text>
        <text x="430" y="200" textAnchor="end">→ Dakar FIR</text>
        <text x="70" y="330">↙ Recife FIR</text>
        <text x="66" y="70">América do Norte ↖</text>
        <text x="414" y="350" textAnchor="end">Europa · África</text>
      </g>
    </svg>

    <figcaption className="text-center text-xs text-white/45 mt-4 max-w-sm mx-auto">
      Esquema ilustrativo da posição do FIR — as fronteiras exatas constam do AIP de
      Cabo Verde (publicado pela AAC/ASA).
    </figcaption>
  </figure>
);

export default FirMap;
