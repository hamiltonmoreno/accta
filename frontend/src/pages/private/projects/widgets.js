import React from 'react';

export const TabBtn = ({ active, label, icon: Icon, onClick, badge, testId }) => (
  <button onClick={onClick} data-testid={testId}
    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-lg transition-all whitespace-nowrap ${
      active ? 'bg-carmesim text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100 hover:text-grafite'
    }`}>
    <Icon className="w-4 h-4" />
    {label}
    {badge > 0 && <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${active ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'}`}>{badge}</span>}
  </button>
);
