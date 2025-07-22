import React, { useMemo } from 'react';
import ThreeWordCloud from './ThreeWordCloud';

const WORD_POOL = [
  'AI','Election','Climate','Sports','Music','Economy','Health','Space','Tech','Policy',
  'Education','Travel','Science','Energy','Art','Film','Food','Weather','Crypto','Market',
  'Startup','Justice','Culture','Media','Security','Trade','Fashion','Gaming','History','Law',
  'China','US','Europe','Africa','Asia','Ocean','Virus','Robot','Data','Privacy'
];

function generateSimulatedWords(n = 20) {
  const shuffled = [...WORD_POOL].sort(() => 0.5 - Math.random());
  const selected = shuffled.slice(0, n);
  return selected.map((text, i) => ({
    text,
    frequency: 1 - i / n // 1.0 (top) to ~0.0 (least)
  }));
}

export default function App() {
  const words = useMemo(() => generateSimulatedWords(20), []);
  return (
    <div style={{ width: '100vw', height: '100vh', background: '#181c20' }}>
      <ThreeWordCloud words={words} />
    </div>
  );
} 