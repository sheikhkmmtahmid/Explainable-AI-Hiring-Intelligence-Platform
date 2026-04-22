export default function LogoIcon({ size = 36, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Background */}
      <rect width="40" height="40" rx="10" fill="#AE0001" />

      {/* Person — head */}
      <circle cx="17" cy="15" r="5" fill="white" />

      {/* Person — shoulders */}
      <path
        d="M7 33c0-5.523 4.477-10 10-10s10 4.477 10 10"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />

      {/* Neural-network nodes (top-right) — represents AI analysis */}
      <circle cx="30" cy="9"  r="2.2" fill="white" fillOpacity="0.95" />
      <circle cx="35" cy="17" r="1.6" fill="white" fillOpacity="0.75" />
      <circle cx="25" cy="6"  r="1.6" fill="white" fillOpacity="0.75" />

      {/* Connecting edges */}
      <line x1="30" y1="9"  x2="35" y2="17" stroke="white" strokeWidth="1.1" strokeOpacity="0.5" />
      <line x1="30" y1="9"  x2="25" y2="6"  stroke="white" strokeWidth="1.1" strokeOpacity="0.5" />
      <line x1="25" y1="6"  x2="35" y2="17" stroke="white" strokeWidth="1.1" strokeOpacity="0.3" />

      {/* Small checkmark badge — represents a hiring decision */}
      <circle cx="30" cy="28" r="6" fill="#D3A625" />
      <path
        d="M27 28.2l2 2 4-4"
        stroke="white"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  )
}
