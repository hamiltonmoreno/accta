import React, { useEffect, useState } from 'react';

export const Countdown = ({ endsAt }) => {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (!endsAt) return null;
  const remaining = Math.max(0, Math.floor((new Date(endsAt).getTime() - now) / 1000));
  const m = Math.floor(remaining / 60);
  const s = String(remaining % 60).padStart(2, '0');
  return (
    <span className={`font-mono text-xs ${remaining <= 10 ? 'text-[#B91C1C]' : 'text-[#3A3A3A]'}`}>
      {m}:{s}
    </span>
  );
};
