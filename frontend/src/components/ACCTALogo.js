import React from 'react';

export const ACCTALogo = ({ variant = 'full', className = '', size = 'md' }) => {
  const sizes = {
    sm: { width: 100, height: 32 },
    md: { width: 140, height: 44 },
    lg: { width: 180, height: 56 },
    xl: { width: 220, height: 68 },
  };

  const { width, height } = sizes[size] || sizes.md;

  if (variant === 'icon') {
    return (
      <svg 
        viewBox="0 0 60 60" 
        className={className}
        style={{ width: height, height: height }}
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* A with airplane trajectory */}
        <path 
          d="M30 8L12 52h8l4-10h12l4 10h8L30 8zm0 14l5 14h-10l5-14z" 
          fill="#C7202F"
        />
        {/* Airplane trajectory line */}
        <path 
          d="M8 30C8 30 15 22 30 22C45 22 52 30 52 30" 
          stroke="#3A3A3A" 
          strokeWidth="2" 
          fill="none"
          strokeLinecap="round"
        />
        {/* Small airplane */}
        <path 
          d="M50 30l-6-2v-2l6-2v2h2v2h-2v2z" 
          fill="#3A3A3A"
        />
      </svg>
    );
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Logo Icon */}
      <div className="relative" style={{ width: height * 0.8, height: height * 0.8 }}>
        <svg 
          viewBox="0 0 50 50" 
          className="w-full h-full"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Letter A base */}
          <path 
            d="M25 5L8 45h6l3-8h16l3 8h6L25 5zm0 12l6 16H19l6-16z" 
            fill="#C7202F"
          />
          {/* Trajectory arc */}
          <path 
            d="M6 26C6 26 12 18 25 18C38 18 44 26 44 26" 
            stroke="#3A3A3A" 
            strokeWidth="2" 
            fill="none"
            strokeLinecap="round"
          />
          {/* Airplane symbol */}
          <g transform="translate(40, 24)">
            <path d="M0 2L8 0V4L0 2Z" fill="#3A3A3A"/>
            <path d="M2 0L4 2L2 4V0Z" fill="#3A3A3A"/>
          </g>
        </svg>
      </div>

      {/* Text */}
      <div className="flex flex-col">
        <span 
          className="font-bold tracking-wider leading-none"
          style={{ 
            fontSize: height * 0.45,
            color: '#C7202F',
            fontFamily: "'Open Sans', sans-serif"
          }}
        >
          ACCTA
        </span>
        <span 
          className="tracking-wide leading-tight"
          style={{ 
            fontSize: height * 0.18,
            color: '#3A3A3A',
            fontFamily: "'Open Sans', sans-serif"
          }}
        >
          CABO VERDE
        </span>
      </div>
    </div>
  );
};

// Simplified horizontal logo
export const ACCTALogoHorizontal = ({ className = '', dark = false }) => {
  const textColor = dark ? '#FFFFFF' : '#3A3A3A';
  const accentColor = '#C7202F';

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <svg width="36" height="36" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
        <path 
          d="M25 5L8 45h6l3-8h16l3 8h6L25 5zm0 12l6 16H19l6-16z" 
          fill={accentColor}
        />
        <path 
          d="M6 26C6 26 12 18 25 18C38 18 44 26 44 26" 
          stroke={textColor} 
          strokeWidth="2" 
          fill="none"
          strokeLinecap="round"
        />
        <g transform="translate(40, 24)">
          <path d="M0 2L8 0V4L0 2Z" fill={textColor}/>
        </g>
      </svg>
      <div className="flex flex-col">
        <span 
          className="font-bold text-xl tracking-wider leading-none"
          style={{ color: accentColor }}
        >
          ACCTA
        </span>
        <span 
          className="text-[10px] tracking-wide"
          style={{ color: textColor }}
        >
          CABO VERDE
        </span>
      </div>
    </div>
  );
};
