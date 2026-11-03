'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { AlertTriangle, Database, FileText, RefreshCw, Search, Trash2, Upload, X } from 'lucide-react'
import { opsApi, type DatasetFile, type DatasetInfo } from '@/lib/api'
import { useAdminError } from '@/lib/use-admin-error'

export default function AdminDatasetPage() {
  const [info, setInfo] = useState<DatasetInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const [query, setQuery] = useState('')
  const [confirmRemove, setConfirmRemove] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const replaceInput = useRef<HTMLInputElement>(null)
  const replaceTarget = useRef<string | null>(null)
  const handleError = useAdminError(setError)

  const load = useCallback(async () => {
    try {
      setInfo(await opsApi.dataset())
      setError(null)
    } catch (e) {
      handleError(e)
    }
  }, [handleError])

  useEffect(() => {
    load()
  }, [load])

  // Poll while a full rebuild runs in the background.
  useEffect(() => {
    if (!info?.index.rebuild.running) return
    const t = setInterval(load, 2000)
    return () => clearInterval(t)
  }, [info?.index.rebuild.running, load])

  async function upload(files: FileList | File[], replace: boolean) {
    setNotice(null)
    setError(null)
    for (const file of Array.from(files)) {
      if (replace && replaceTarget.current && file.name !== replaceTarget.current) {
        setError(`To replace "${replaceTarget.current}", choose a file with exactly the same name (you picked "${file.name}").`)
        continue
      }
      setBusy(file.name)
      try {
        const res = await opsApi.upload(file, replace)
        setNotice(`${res.status === 'replaced' ? 'Replaced' : 'Added'} "${res.name}" (${res.chunks} chunk${res.chunks === 1 ? '' : 's'}). The chatbot can use it now.`)
      } catch (e) {
        handleError(e)
      }
    }
    setBusy(null)
    replaceTarget.current = null
    await load()
  }

  async function remove(name: string) {
    setConfirmRemove(null)
    setBusy(name)
    try {
      const res = await opsApi.remove(name)
      setNotice(`Removed "${name}" (${res.chunks_removed} chunks). A copy is kept in the backend's data/doc_history folder.`)
    } catch (e) {
      handleError(e)
    }
    setBusy(null)
    await load()
  }

  async function rebuild() {
    setNotice(null)
    try {
      await opsApi.rebuild()
    } catch (e) {
      handleError(e)
    }
    await load()
  }

  const idx = info?.index
  const mismatch = !!idx?.embedder && idx.embedder !== idx.current_embedder
  const q = query.trim().toLowerCase()
  const files = (info?.files ?? []).filter((f) => !q || f.name.toLowerCase().includes(q))

  return (
    <div className="view admin-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">ADMIN · DATASET</p>
          <h1>What the chatbot knows.</h1>
          <p className="view-sub">Add, replace or remove official documents. Changes reach the chatbot immediately and are logged under your name.</p>
        </div>
      </div>

      {idx && (
        <div className="stat-tiles">
          <div className="stat-tile">
            <span>Documents</span>
            <strong>{info!.files.length}</strong>
          </div>
          <div className="stat-tile">
            <span>Readable by the chatbot</span>
            <strong>
              {info!.files.filter((f) => f.chunks).length}/{info!.files.length}
            </strong>
            {idx.exists && info!.files.some((f) => f.supported && !f.chunks) && <small>others have no text layer (scanned?)</small>}
          </div>
          <div className="stat-tile">
            <span>Indexed chunks</span>
            <strong>{idx.exists ? (idx.total_chunks ?? '—') : 'No index'}</strong>
          </div>
          <div className="stat-tile">
            <span>Community posts in dataset</span>
            <strong>{info!.community_posts_in_dataset}</strong>
            <Link href="/admin/community" className="inline-link">
              Manage
            </Link>
          </div>
          <div className="stat-tile">
            <span>Last built</span>
            <strong className="small">{idx.built_at ? new Date(idx.built_at).toLocaleString() : '—'}</strong>
            <small>{idx.embedder ?? idx.current_embedder}</small>
          </div>
        </div>
      )}

      {idx && (!idx.exists || mismatch) && (
        <div className="community-error" role="alert">
          <span>
            <AlertTriangle className="inline-icon" />{' '}
            {!idx.exists
              ? "There's no chatbot index yet, so the chatbot can't search these documents. Build it once to start."
              : `The index was built with ${idx.embedder} but the server now uses ${idx.current_embedder}. Rebuild so searches work properly.`}
          </span>
          <button className="text-button" onClick={rebuild} disabled={idx.rebuild.running}>
            {idx.exists ? 'Rebuild now' : 'Build index'}
          </button>
        </div>
      )}

      <div
        className={`upload-zone ${dragging ? 'dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          if (e.dataTransfer.files.length) upload(e.dataTransfer.files, false)
        }}
      >
        <Upload />
        <div>
          <strong>Drop files here or</strong>{' '}
          <button className="text-button" onClick={() => fileInput.current?.click()} disabled={!!busy}>
            choose files
          </button>
          <p>
            {info ? info.supported_extensions.join(', ').toUpperCase().replace(/\./g, '') : 'PDF, DOCX, CSV, TXT, MD'} up to {info?.max_mb ?? 25} MB. Old
            Word .doc files must be saved as .docx or PDF first.
          </p>
        </div>
        <input
          ref={fileInput}
          type="file"
          multiple
          hidden
          accept=".pdf,.docx,.csv,.txt,.md"
          onChange={(e) => {
            if (e.target.files?.length) upload(e.target.files, false)
            e.target.value = ''
          }}
        />
        <input
          ref={replaceInput}
          type="file"
          hidden
          accept=".pdf,.docx,.csv,.txt,.md"
          onChange={(e) => {
            if (e.target.files?.length) upload(e.target.files, true)
            e.target.value = ''
          }}
        />
      </div>

      {busy && <p className="view-sub">Working on &quot;{busy}&quot;…</p>}
      {idx?.rebuild.running && (
        <p className="view-sub">
          <RefreshCw className="inline-icon spin" /> Rebuilding the whole index… this can take a few minutes for many documents.
        </p>
      )}
      {idx?.rebuild.error && !idx.rebuild.running && <p className="community-error">Last rebuild failed: {idx.rebuild.error}</p>}
      {notice && <p className="admin-notice">{notice}</p>}
      {error && <p className="community-error">{error}</p>}

      <div className="dataset-toolbar">
        <div className="large-search community-search">
          <Search />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter documents" aria-label="Filter documents" />
          {q && (
            <button className="icon-action" onClick={() => setQuery('')} aria-label="Clear filter">
              <X size={14} />
            </button>
          )}
        </div>
        <button className="network-action connected" onClick={rebuild} disabled={!!idx?.rebuild.running} title="Re-read every document and rebuild the chatbot index">
          <RefreshCw /> Full rebuild
        </button>
      </div>

      <div className="dataset-table" role="table" aria-label="Dataset documents">
        <div className="dataset-row head" role="row">
          <span>Document</span>
          <span>Size</span>
          <span>Chunks</span>
          <span>Last change</span>
          <span />
        </div>
        {files.map((f: DatasetFile) => (
          <div key={f.name} className="dataset-row" role="row">
            <span className="dataset-name">
              <FileText />
              <span>
                {f.name}
                <small>
                  {f.type} · v{f.version}
                  {!f.supported && ' · not readable by the chatbot'}
                </small>
              </span>
            </span>
            <span>{f.size}</span>
            <span>
              {f.chunks ? (
                f.chunks
              ) : idx?.exists && f.supported && !idx.rebuild.running ? (
                <span className="dataset-unreadable" title="The chatbot can't read this file. If it's a scanned PDF, upload a text-based version (or a .docx) with Replace.">
                  No text
                </span>
              ) : (
                '—'
              )}
            </span>
            <span className="dataset-change">{f.last_change ? `${f.last_change.action === 'replace' ? 'Replaced' : 'Added'} by ${f.last_change.by} · ${f.last_change.when}` : `Original · ${f.modified}`}</span>
            <span className="dataset-actions">
              {confirmRemove === f.name ? (
                <>
                  <button className="text-button" onClick={() => setConfirmRemove(null)}>
                    Cancel
                  </button>
                  <button className="community-ask-btn small danger" onClick={() => remove(f.name)}>
                    Remove
                  </button>
                </>
              ) : (
                <>
                  <button
                    className="icon-action"
                    title="Replace with a new version (same file name)"
                    aria-label={`Replace ${f.name}`}
                    disabled={!!busy}
                    onClick={() => {
                      replaceTarget.current = f.name
                      replaceInput.current?.click()
                    }}
                  >
                    <Upload size={14} />
                  </button>
                  <button className="icon-action danger" title="Remove from the dataset" aria-label={`Remove ${f.name}`} disabled={!!busy} onClick={() => setConfirmRemove(f.name)}>
                    <Trash2 size={14} />
                  </button>
                </>
              )}
            </span>
          </div>
        ))}
        {info && files.length === 0 && (
          <p className="view-sub dataset-empty">
            <Database className="inline-icon" /> {q ? 'No documents match.' : 'No documents yet. Upload the first one above.'}
          </p>
        )}
      </div>
    </div>
  )
}
