'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowUpRight, Lock } from 'lucide-react'
import { ProfileEntriesEditor } from '@/components/profile-entries-editor'
import { currentUser, meApi, type ProfileEntry } from '@/lib/api'
import { mitClubs } from '@/lib/clubs'
import { avatarChoices, defaultProfile, interestOptions, type Profile } from '@/lib/mock-data'
import { forgetStudentOnThisDevice } from '@/lib/session'
import { useLocalState } from '@/lib/use-local-state'

// Clubs and projects live on the server (other students see them); this is a cached copy.
type PublicDetails = { clubs: ProfileEntry[]; projects: ProfileEntry[] }

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
  const [confirmingReset, setConfirmingReset] = useState(false)
  const router = useRouter()
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleteWord, setDeleteWord] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const [details, setDetails] = useLocalState<PublicDetails>('mitra_public_details', { clubs: [], projects: [] })
  const [draftClubs, setDraftClubs] = useState<ProfileEntry[]>([])
  const [draftProjects, setDraftProjects] = useState<ProfileEntry[]>([])
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  useEffect(() => {
    currentUser()
      .then((u) => setDetails({ clubs: u.clubs ?? [], projects: u.projects ?? [] }))
      .catch(() => {}) // offline: keep the cached copy
  }, [setDetails])

  function toggle(key: keyof SettingsFlags) {
    setFlags((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  function startEditing() {
    setDraftAvatar(profile.avatar)
    setDraftInterests(profile.interests)
    setCustomInterest('')
    setDraftClubs(details.clubs)
    setDraftProjects(details.projects)
    setSaveError('')
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

  async function saveProfile() {
    setSaving(true)
    setSaveError('')
    try {
      const saved = await meApi.updateProfile({ clubs: draftClubs, projects: draftProjects })
      setDetails({ clubs: saved.clubs, projects: saved.projects })
      setProfile((prev) => ({ ...prev, avatar: draftAvatar, interests: draftInterests }))
      setEditing(false)
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : 'Could not save your profile. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  async function deleteAccount() {
    setDeleting(true)
    setDeleteError('')
    try {
      await meApi.deleteAccount(deleteWord.trim())
    } catch (e) {
      setDeleteError(e instanceof Error ? e.message : "Couldn't delete your account. Please try again.")
      setDeleting(false)
      return
    }
    forgetStudentOnThisDevice()
    router.replace('/')
  }

  function resetInterests() {
    setProfile((prev) => ({ ...prev, interests: [] }))
    // An open profile editor holds a copy of the old interests; saving it would undo the reset.
    setEditing(false)
    setConfirmingReset(false)
    setResetMessage('Interest profile reset. Add interests again from Edit profile.')
    setTimeout(() => setResetMessage(''), 4000)
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
                {details.clubs.length > 0 && <small>Clubs: {details.clubs.map((c) => c.name).join(', ')}</small>}
                {details.projects.length > 0 && (
                  <small>Student projects: {details.projects.map((p) => p.name).join(', ')}</small>
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
                <strong>Clubs</strong>
                <ProfileEntriesEditor
                  entries={draftClubs}
                  onChange={setDraftClubs}
                  suggestions={mitClubs}
                  namePlaceholder="Club name, e.g. IECSE"
                  rolePlaceholder="Your role (optional)"
                />
              </div>

              <div className="profile-edit-section">
                <strong>Student projects</strong>
                <ProfileEntriesEditor
                  entries={draftProjects}
                  onChange={setDraftProjects}
                  namePlaceholder="Project or team, e.g. Formula Manipal"
                  rolePlaceholder="Your role (optional)"
                />
                <small>Clubs and student projects are shown on your public profile to other MITra students.</small>
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

              {saveError && <p className="field-error">{saveError}</p>}
              <div className="composer-actions">
                <button className="text-button" onClick={() => setEditing(false)}>
                  Cancel
                </button>
                <button className="community-ask-btn small" onClick={saveProfile} disabled={saving}>
                  {saving ? 'Saving…' : 'Save changes'}
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
          <div className={`settings-card ${confirmingReset ? 'confirming' : ''}`}>
            <div>
              <strong>Reset interest profile</strong>
              <span>
                {resetMessage ||
                  (profile.interests.length === 0
                    ? 'No interests saved right now.'
                    : 'Clear learned preferences and start fresh.')}
              </span>
              {confirmingReset && (
                <div className="reset-confirm" role="alertdialog" aria-label="Confirm interest profile reset">
                  <p>
                    This will remove your {profile.interests.length} interest{profile.interests.length === 1 ? '' : 's'} (
                    {profile.interests.join(', ')}), so recommendations start from scratch. Your saved items, posts and connections
                    won&apos;t be affected. This can&apos;t be undone.
                  </p>
                  <div className="composer-actions">
                    <button className="text-button" onClick={() => setConfirmingReset(false)} autoFocus>
                      Cancel
                    </button>
                    <button className="community-ask-btn small danger" onClick={resetInterests}>
                      Yes, reset
                    </button>
                  </div>
                </div>
              )}
            </div>
            {!confirmingReset && (
              <button
                className="settings-action"
                onClick={() => {
                  setResetMessage('')
                  setConfirmingReset(true)
                }}
                disabled={profile.interests.length === 0}
              >
                Reset
              </button>
            )}
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

        <section>
          <h3>Account</h3>
          <div className={`settings-card ${confirmingDelete ? 'confirming' : ''}`}>
            <div>
              <strong>Delete account</strong>
              <span>Permanently delete your MITra account and your personal data.</span>
              {confirmingDelete && (
                <div className="reset-confirm" role="alertdialog" aria-label="Confirm account deletion">
                  <p>
                    This permanently deletes your account, chat history, connections, private messages, votes and
                    notifications. Your Community questions and answers stay in their threads as &ldquo;Former member&rdquo;.
                    This can&apos;t be undone.
                  </p>
                  <label className="delete-confirm-field">
                    Type <b>DELETE</b> to confirm
                    <input
                      value={deleteWord}
                      onChange={(e) => setDeleteWord(e.target.value)}
                      autoComplete="off"
                      autoFocus
                      disabled={deleting}
                    />
                  </label>
                  {deleteError && <p className="community-error">{deleteError}</p>}
                  <div className="composer-actions">
                    <button
                      className="text-button"
                      onClick={() => {
                        setConfirmingDelete(false)
                        setDeleteWord('')
                        setDeleteError('')
                      }}
                      disabled={deleting}
                    >
                      Cancel
                    </button>
                    <button
                      className="community-ask-btn small danger"
                      onClick={deleteAccount}
                      disabled={deleteWord.trim() !== 'DELETE' || deleting}
                    >
                      {deleting ? 'Deleting…' : 'Delete my account'}
                    </button>
                  </div>
                </div>
              )}
            </div>
            {!confirmingDelete && (
              <button className="settings-action danger" onClick={() => setConfirmingDelete(true)}>
                Delete
              </button>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
