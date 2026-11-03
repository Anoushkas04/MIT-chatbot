'use client'

import { useState } from 'react'
import { ArrowUpRight, Lock } from 'lucide-react'
import { avatarChoices, defaultProfile, interestOptions, type Profile } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

type SettingsFlags = {
  personalization: boolean
  showInferred: boolean
  notifications: boolean
}

const defaultFlags: SettingsFlags = { personalization: true, showInferred: true, notifications: true }

function Toggle({ on, onClick }: { on: boolean; onClick: () => void }) {
  return (
    <button className={`toggle ${on ? 'on' : ''}`} role="switch" aria-checked={on} onClick={onClick}>
      <i />
    </button>
  )
}

export default function SettingsPage() {
  const [profile, setProfile] = useLocalState<Profile>('mitra_profile', defaultProfile)
  const [flags, setFlags] = useLocalState<SettingsFlags>('mitra_settings', defaultFlags)
  const [editing, setEditing] = useState(false)
  const [draftAvatar, setDraftAvatar] = useState(profile.avatar)
  const [draftInterests, setDraftInterests] = useState<string[]>(profile.interests)
  const [customInterest, setCustomInterest] = useState('')
  const [resetMessage, setResetMessage] = useState('')

  function toggle(key: keyof SettingsFlags) {
    setFlags((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  function startEditing() {
    setDraftAvatar(profile.avatar)
    setDraftInterests(profile.interests)
    setCustomInterest('')
    setEditing(true)
  }

  function toggleInterest(interest: string) {
    setDraftInterests((prev) => (prev.includes(interest) ? prev.filter((x) => x !== interest) : [...prev, interest]))
  }

  function addCustomInterest() {
    const value = customInterest.trim()
    if (!value || draftInterests.includes(value)) return
    setDraftInterests((prev) => [...prev, value])
    setCustomInterest('')
  }

  function saveProfile() {
    setProfile((prev) => ({ ...prev, avatar: draftAvatar, interests: draftInterests }))
    setEditing(false)
  }

  function resetInterests() {
    setProfile((prev) => ({ ...prev, interests: [] }))
    setResetMessage('Interest profile reset.')
    setTimeout(() => setResetMessage(''), 2500)
  }

  return (
    <div className="view settings-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">SETTINGS</p>
          <h1>Make MITra yours.</h1>
          <p className="view-sub">Manage your account, preferences and privacy.</p>
        </div>
      </div>
      <div className="settings-list">
        <section>
          <h3>Profile</h3>
          {!editing ? (
            <div className="settings-card profile-setting">
              <div className="header-avatar large" style={{ background: profile.avatar.color }}>
                {profile.avatar.emoji}
              </div>
              <div>
                <strong>{profile.name}</strong>
                <span>{profile.learnerId}</span>
                <small>
                  {profile.branch} · {profile.semester}
                </small>
                {profile.interests.length > 0 && (
                  <div className="tag-row">
                    {profile.interests.map((i) => (
                      <span key={i} className="tag-chip">
                        {i}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <button onClick={startEditing}>
                Edit profile <ArrowUpRight />
              </button>
            </div>
          ) : (
            <div className="settings-card profile-setting editing">
              <div className="profile-edit-section">
                <strong>Profile picture</strong>
                <div className="avatar-picker">
                  {avatarChoices.map((a) => (
                    <button
                      key={a.emoji}
                      className={draftAvatar.emoji === a.emoji ? 'active' : ''}
                      style={{ background: a.color }}
                      onClick={() => setDraftAvatar(a)}
                      aria-label={`Use ${a.emoji} avatar`}
                    >
                      {a.emoji}
                    </button>
                  ))}
                </div>
              </div>
              <div className="profile-edit-section">
                <strong>Interests</strong>
                <div className="tag-picker">
                  {interestOptions.map((i) => (
                    <button key={i} className={draftInterests.includes(i) ? 'active' : ''} onClick={() => toggleInterest(i)}>
                      {i}
                    </button>
                  ))}
                  {draftInterests
                    .filter((i) => !(interestOptions as readonly string[]).includes(i))
                    .map((i) => (
                      <button key={i} className="active" onClick={() => toggleInterest(i)}>
                        {i}
                      </button>
                    ))}
                </div>
                <div className="custom-interest-row">
                  <input
                    value={customInterest}
                    onChange={(e) => setCustomInterest(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addCustomInterest()
                      }
                    }}
                    placeholder="Type an interest and press Enter..."
                  />
                  <button className="text-button" onClick={addCustomInterest}>
                    Add
                  </button>
                </div>
              </div>

              <div className="profile-edit-section">
                <strong>
                  <Lock /> Fixed details
                </strong>
                <div className="locked-fields">
                  <div>
                    <span>Learner ID</span>
                    <span>{profile.learnerId}</span>
                  </div>
                  <div>
                    <span>Registration number</span>
                    <span>{profile.regNumber}</span>
                  </div>
                  <div>
                    <span>Branch</span>
                    <span>{profile.branch}</span>
                  </div>
                  <div>
                    <span>Semester</span>
                    <span>{profile.semester}</span>
                  </div>
                </div>
                <small>These are set by your institutional record and can&apos;t be edited here.</small>
              </div>

              <div className="composer-actions">
                <button className="text-button" onClick={() => setEditing(false)}>
                  Cancel
                </button>
                <button className="community-ask-btn small" onClick={saveProfile}>
                  Save changes
                </button>
              </div>
            </div>
          )}
        </section>

        <section>
          <h3>Personalization</h3>
          <div className="settings-card">
            <div>
              <strong>Behavioral personalization</strong>
              <span>Use your saves and interests to improve recommendations.</span>
            </div>
            <Toggle on={flags.personalization} onClick={() => toggle('personalization')} />
          </div>
          <div className="settings-card">
            <div>
              <strong>Show inferred interests</strong>
              <span>See the topics MITra thinks you might like.</span>
            </div>
            <Toggle on={flags.showInferred} onClick={() => toggle('showInferred')} />
          </div>
          <div className="settings-card">
            <div>
              <strong>Reset interest profile</strong>
              <span>{resetMessage || 'Clear learned preferences and start fresh.'}</span>
            </div>
            <button className="settings-action" onClick={resetInterests}>
              Reset
            </button>
          </div>
        </section>

        <section>
          <h3>Notifications</h3>
          <div className="settings-card">
            <div>
              <strong>Important campus updates</strong>
              <span>Deadlines, notices and relevant announcements.</span>
            </div>
            <Toggle on={flags.notifications} onClick={() => toggle('notifications')} />
          </div>
        </section>
      </div>
    </div>
  )
}
