'use client'

import { useCallback, useEffect, useState } from 'react'
import { opsApi, type DayValue, type Insights } from '@/lib/api'
import { useAdminError } from '@/lib/use-admin-error'

const pct = (v: number | null) => (v === null ? '—' : `${Math.round(v * 100)}%`)
const fmtDay = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })

/** Single-series daily bars with a per-bar hover tooltip and a table fallback. */
function DailyBars({ title, data, unit }: { title: string; data: DayValue[]; unit: string }) {
  const [hover, setHover] = useState<number | null>(null)
  const W = 640
  const H = 160
  const pad = { top: 14, right: 8, bottom: 22, left: 30 }
  const max = Math.max(1, ...data.map((d) => d.value))
  const plotW = W - pad.left - pad.right
  const plotH = H - pad.top - pad.bottom
  const slot = plotW / data.length
  const barW = Math.max(2, Math.min(14, slot - 2)) // 2px surface gap between neighbours
  const y = (v: number) => pad.top + plotH - (v / max) * plotH
  const total = data.reduce((a, d) => a + d.value, 0)
  const ticks = data.length > 1 ? [0, Math.floor((data.length - 1) / 2), data.length - 1] : [0]

  return (
    <figure className="viz">
      <figcaption>
        <strong>{title}</strong>
        <span>
          {total} {unit} in {data.length} days
        </span>
      </figcaption>
      <div className="viz-plot">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${title}: ${total} ${unit} over ${data.length} days`} onMouseLeave={() => setHover(null)}>
          {/* recessive grid: baseline and the max line only */}
          <line x1={pad.left} x2={W - pad.right} y1={y(0)} y2={y(0)} className="viz-axis" />
          <line x1={pad.left} x2={W - pad.right} y1={y(max)} y2={y(max)} className="viz-grid" />
          <text x={pad.left - 6} y={y(max) + 3} className="viz-tick" textAnchor="end">
            {max}
          </text>
          <text x={pad.left - 6} y={y(0) + 3} className="viz-tick" textAnchor="end">
            0
          </text>
          {data.map((d, i) => {
            const cx = pad.left + slot * i + slot / 2
            const top = y(d.value)
            const h = y(0) - top
            const r = Math.min(4, barW / 2, h)
            const x0 = cx - barW / 2
            // rounded data-end, square at the baseline
            const path = h > 0 ? `M${x0},${y(0)} V${top + r} Q${x0},${top} ${x0 + r},${top} H${x0 + barW - r} Q${x0 + barW},${top} ${x0 + barW},${top + r} V${y(0)} Z` : ''
            return (
              <g key={d.date}>
                {path && <path d={path} className={`viz-bar ${hover === i ? 'is-hover' : ''}`} />}
                {/* hit target: the whole column, bigger than the mark */}
                <rect x={pad.left + slot * i} y={pad.top} width={slot} height={plotH} fill="transparent" onMouseEnter={() => setHover(i)} />
              </g>
            )
          })}
          {ticks.map((i) => (
            <text key={i} x={pad.left + slot * i + slot / 2} y={H - 6} className="viz-tick" textAnchor={i === 0 ? 'start' : i === data.length - 1 ? 'end' : 'middle'}>
              {fmtDay(data[i].date)}
            </text>
          ))}
        </svg>
        {hover !== null && (
          <div className="viz-tooltip" style={{ left: `${((pad.left + slot * hover + slot / 2) / W) * 100}%` }}>
            <strong>{data[hover].value}</strong> {unit}
            <span>{fmtDay(data[hover].date)}</span>
          </div>
        )}
      </div>
      <details className="viz-table">
        <summary>Show as table</summary>
        <table>
          <thead>
            <tr>
              <th>Day</th>
              <th>{unit}</th>
            </tr>
          </thead>
          <tbody>
            {data
              .filter((d) => d.value > 0)
              .map((d) => (
                <tr key={d.date}>
                  <td>{fmtDay(d.date)}</td>
                  <td>{d.value}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </details>
    </figure>
  )
}

/** Ranked horizontal bars (magnitude by category), each labelled with its value. */
function RankBars({ title, items, empty }: { title: string; items: [string, number][]; empty: string }) {
  const max = Math.max(1, ...items.map(([, n]) => n))
  return (
    <figure className="viz">
      <figcaption>
        <strong>{title}</strong>
      </figcaption>
      {items.length === 0 ? (
        <p className="view-sub">{empty}</p>
      ) : (
        <ol className="rank-bars">
          {items.map(([label, n]) => (
            <li key={label} title={`${label}: ${n}`}>
              <span className="rank-label">{label}</span>
              <span className="rank-track">
                <span className="rank-fill" style={{ width: `${(n / max) * 100}%` }} />
              </span>
              <span className="rank-value">{n}</span>
            </li>
          ))}
        </ol>
      )}
    </figure>
  )
}

// Categorical slots (dataviz reference palette, fixed order, validated light-mode adjacent
// pairs). Three sit below 3:1 on the card, so every slice is also named in the legend.
const SLICE_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']
const OTHER_COLOR = '#a7aaa4'
const MAX_SLICES = 6 // 5 named + "Other": past ~6 segments a pie stops reading part-to-whole

/** Part-to-whole donut: top 5 named, the rest folded into "Other"; the centre shows the
 * total and the legend carries each name, count and share. */
function PieChart({ title, items, empty, unit }: { title: string; items: [string, number][]; empty: string; unit: string }) {
  const [hover, setHover] = useState<number | null>(null)
  const sorted = [...items].filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1])
  if (sorted.length === 0) return <RankBars title={title} items={[]} empty={empty} />
  const named = sorted.slice(0, MAX_SLICES - 1)
  const rest = sorted.slice(MAX_SLICES - 1).reduce((a, [, n]) => a + n, 0)
  const slices = rest > 0 ? [...named, ['Other', rest] as [string, number]] : named
  const total = slices.reduce((a, [, n]) => a + n, 0)
  const color = (i: number) => (rest > 0 && i === slices.length - 1 ? OTHER_COLOR : SLICE_COLORS[i])

  const C = 80
  const R = 74 // outer radius
  const r = 46 // inner radius: the hole holds the total
  let angle = -Math.PI / 2 // start at 12 o'clock, clockwise
  const pt = (rad: number, a: number) => `${(C + rad * Math.cos(a)).toFixed(2)},${(C + rad * Math.sin(a)).toFixed(2)}`
  const paths = slices.map(([, n]) => {
    const sweep = (n / total) * Math.PI * 2
    const a0 = angle
    const a1 = angle + sweep
    angle = a1
    const large = sweep > Math.PI ? 1 : 0
    return `M${pt(R, a0)} A${R},${R} 0 ${large} 1 ${pt(R, a1)} L${pt(r, a1)} A${r},${r} 0 ${large} 0 ${pt(r, a0)} Z`
  })
  const focus = hover ?? null

  return (
    <figure className="viz">
      <figcaption>
        <strong>{title}</strong>
      </figcaption>
      <div className="pie-layout">
        <div className="viz-plot pie-plot">
          <svg viewBox="0 0 160 160" role="img" aria-label={`${title}: ${slices.map(([l, n]) => `${l} ${n}`).join(', ')}`} onMouseLeave={() => setHover(null)}>
            {slices.length === 1 ? (
              // One category: a full ring (an arc can't draw a complete circle).
              <circle cx={C} cy={C} r={(R + r) / 2} fill="none" stroke={color(0)} strokeWidth={R - r} className="pie-ring" onMouseEnter={() => setHover(0)} />
            ) : (
              paths.map((d, i) => (
                <path key={slices[i][0]} d={d} fill={color(i)} className={`pie-slice ${focus !== null && focus !== i ? 'dim' : ''}`} onMouseEnter={() => setHover(i)} />
              ))
            )}
            {/* Centre: the total, or the hovered slice's share */}
            <text x={C} y={C - 2} textAnchor="middle" className="pie-centre-value">
              {focus === null ? total : `${Math.round((slices[focus][1] / total) * 100)}%`}
            </text>
            <text x={C} y={C + 14} textAnchor="middle" className="pie-centre-label">
              {focus === null ? unit : slices[focus][0].length > 14 ? `${slices[focus][0].slice(0, 13)}…` : slices[focus][0]}
            </text>
          </svg>
        </div>
        <ul className="pie-legend">
          {slices.map(([label, n], i) => (
            <li key={label} className={hover === i ? 'is-hover' : ''} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} title={label}>
              <i style={{ background: color(i) }} aria-hidden />
              <span className="pie-label">{label}</span>
              <span className="pie-value">
                {n} <small>{Math.round((n / total) * 100)}%</small>
              </span>
            </li>
          ))}
        </ul>
      </div>
    </figure>
  )
}

function Tile({ label, value, note }: { label: string; value: string | number; note?: string }) {
  return (
    <div className="stat-tile">
      <span>{label}</span>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  )
}

export default function AdminInsightsPage() {
  const [days, setDays] = useState<7 | 30 | 90>(30)
  const [data, setData] = useState<Insights | null>(null)
  const [error, setError] = useState<string | null>(null)
  const handleError = useAdminError(setError)

  const load = useCallback(async () => {
    try {
      setData(await opsApi.insights(days))
      setError(null)
    } catch (e) {
      handleError(e)
    }
  }, [days, handleError])

  useEffect(() => {
    load()
  }, [load])

  const c = data?.chat
  const co = data?.community

  return (
    <div className="view admin-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">ADMIN · INSIGHTS</p>
          <h1>How MITra is being used.</h1>
          <p className="view-sub">What students ask, how well the chatbot answers, community health and safety, from live data.</p>
        </div>
        <div className="tag-picker" role="group" aria-label="Time range">
          {([7, 30, 90] as const).map((d) => (
            <button key={d} className={days === d ? 'active' : ''} onClick={() => setDays(d)}>
              {d} days
            </button>
          ))}
        </div>
      </div>
      {error && <p className="community-error">{error}</p>}
      {!data && !error && <p className="view-sub">Loading…</p>}

      {data && c && co && (
        <>
          <h3 className="insights-heading">Chatbot</h3>
          <div className="stat-tiles">
            <Tile label="Questions asked" value={c.questions} />
            <Tile label="Low-confidence answers" value={pct(c.low_confidence_rate)} note={c.answers ? `of ${c.answers} answers` : 'no answers yet'} />
            <Tile label="Marked helpful" value={pct(c.helpful_rate)} />
            <Tile label="Feedback rating" value={c.avg_rating === null ? '—' : `${c.avg_rating} / 5`} note={`${c.feedback_count} feedback`} />
          </div>
          <DailyBars title="Questions to the chatbot per day" data={c.per_day} unit="questions" />
          <PieChart title="Top topics" items={c.topics} empty="No questions in this period." unit="questions" />
          <figure className="viz">
            <figcaption>
              <strong>Knowledge gaps</strong>
              <span>Questions the chatbot couldn&apos;t answer confidently. Add a document or verify a Community answer to close them.</span>
            </figcaption>
            {c.knowledge_gaps.length === 0 ? (
              <p className="view-sub">No open gaps.</p>
            ) : (
              <table className="gap-table">
                <thead>
                  <tr>
                    <th>Question</th>
                    <th>Asked</th>
                    <th>Category</th>
                  </tr>
                </thead>
                <tbody>
                  {c.knowledge_gaps.map((g) => (
                    <tr key={g.question}>
                      <td>{g.question}</td>
                      <td>{g.times_asked}×</td>
                      <td>{g.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </figure>

          <h3 className="insights-heading">Community</h3>
          <div className="stat-tiles">
            <Tile label="New questions" value={co.questions} />
            <Tile label="Answers & replies" value={co.answers} note={`${co.official_replies} official`} />
            <Tile label="Still unanswered" value={pct(co.unanswered_rate)} />
            <Tile label="Median time to first answer" value={co.median_hours_to_first_answer === null ? '—' : `${co.median_hours_to_first_answer} h`} />
          </div>
          <DailyBars title="New Community questions per day" data={co.questions_per_day} unit="questions" />
          <div className="insights-grid">
            <PieChart title="Most-used tags" items={co.top_tags} empty="No tagged questions in this period." unit="tag uses" />
            <RankBars title="Reports by reason" items={data.safety.by_reason} empty="No reports in this period. 🎉" />
          </div>

          <h3 className="insights-heading">Accounts & safety</h3>
          <div className="stat-tiles">
            <Tile label="New sign-ups" value={data.accounts.signups} />
            <Tile label="Reports" value={data.safety.reports} />
            <Tile label="Warnings sent" value={data.safety.warnings} />
            <Tile label="Suspensions" value={data.safety.suspensions} note={`${co.removed} posts/replies removed`} />
          </div>
          <DailyBars title="New student sign-ups per day" data={data.accounts.signups_per_day} unit="sign-ups" />
        </>
      )}
    </div>
  )
}
