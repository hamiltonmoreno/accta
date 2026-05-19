import React from 'react';
import { CheckCircle } from 'lucide-react';

export const PollResults = ({ poll, results }) => {
  if (!results) return null;

  return (
    <div className="mt-4 pt-4 border-t border-[#E5E7EB]">
      <div className="text-sm font-mono text-[#6B7280] mb-4">
        Total de votos: {results.total_votes}
      </div>
      <div className="space-y-3">
        {poll.options.map((option) => {
          const voteCount = results.results[option.id] || 0;
          const percent = results.total_votes > 0 
            ? (voteCount / results.total_votes) * 100 
            : 0;
          
          return (
            <div key={option.id}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="font-manrope">{option.label}</span>
                <span className="font-mono text-[#6B7280]">
                  {voteCount} votos ({percent.toFixed(1)}%)
                </span>
              </div>
              <div className="h-2 bg-[#F5F5F5] rounded-full overflow-hidden">
                <div
                  className="h-full bg-carmesim rounded-full transition-all duration-500"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
