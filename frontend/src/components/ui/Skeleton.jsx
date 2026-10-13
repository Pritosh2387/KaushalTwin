import React from 'react';

export function Skeleton({ className = '', ...props }) {
  return (
    <div
      className={`animate-pulse bg-zinc-900/80 rounded-none border border-white/5 ${className}`}
      {...props}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-[#050505] rounded-none border border-white/10 p-6 space-y-4 specular-top-edge">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-6 w-16" />
      </div>
      <Skeleton className="h-4 w-2/3" />
      <div className="space-y-2 pt-2">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
      </div>
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-24" />
      </div>
    </div>
  );
}

export function SkeletonTableRows({ rows = 5, cols = 4 }) {
  return (
    <tbody className="divide-y divide-white/5">
      {Array.from({ length: rows }).map((_, rIdx) => (
        <tr key={rIdx} className="hover:bg-white/[0.02]">
          {Array.from({ length: cols }).map((_, cIdx) => (
            <td key={cIdx} className="px-6 py-4">
              <Skeleton className="h-4 w-full max-w-[140px]" />
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  );
}

export default Skeleton;
