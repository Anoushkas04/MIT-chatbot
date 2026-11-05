import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Logo } from '@/components/logo'
import { GUIDELINES_UPDATED, guidelineSections } from '@/lib/community-guidelines'

export const metadata: Metadata = { title: 'Community Guidelines · MITra' }

// Public (outside the signed-in app) so it can be read from the sign-up form.
export default function GuidelinesPage() {
  return (
    <main className="guidelines-shell">
      <div className="guidelines-top">
        <Link href="/" className="text-button">
          <ArrowLeft /> Back to MITra
        </Link>
        <Logo />
      </div>
      <header className="guidelines-head">
        <p className="section-kicker">COMMUNITY GUIDELINES</p>
        <h1>Keep MITra useful, kind and safe.</h1>
        <p className="view-sub">
          MITra is for MIT Manipal students to ask, answer and connect. These guidelines apply everywhere in MITra:
          Community posts, answers and replies, your profile, and private messages. Last updated {GUIDELINES_UPDATED}.
        </p>
        <nav className="guidelines-toc" aria-label="Sections">
          {guidelineSections.map((s, i) => (
            <a key={s.id} href={`#${s.id}`}>
              {i + 1}. {s.title}
            </a>
          ))}
        </nav>
      </header>
      <div className="guidelines-list">
        {guidelineSections.map((s, i) => (
          <section key={s.id} id={s.id} className="deadline-card guidelines-section">
            <p className="section-kicker">{String(i + 1).padStart(2, '0')}</p>
            <h2>{s.title}</h2>
            {s.intro && <p className="guidelines-intro">{s.intro}</p>}
            <ul>
              {s.points.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </section>
        ))}
      </div>
      <p className="view-sub guidelines-foot">
        Questions about these guidelines? Ask in Community, or contact the MITra team through a plea or appeal if your
        account is affected.
      </p>
    </main>
  )
}
