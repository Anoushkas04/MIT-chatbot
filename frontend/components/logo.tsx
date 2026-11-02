export function Logo({ light = false }: { light?: boolean }) {
  return (
    <div className={`brand ${light ? 'brand-light' : ''}`}>
      <span className="brand-mark">M</span>
      <span>
        MIT<span className="brand-accent">ra</span>
      </span>
    </div>
  )
}
