'use client'

import { useEffect, useRef } from 'react'

export type ConfirmRequest = {
  title: string
  message: string
  confirmLabel: string
  onConfirm: () => void
}

/** In-app replacement for window.confirm: Escape or a click outside cancels. */
export function ConfirmDialog({ request, onClose }: { request: ConfirmRequest | null; onClose: () => void }) {
  const cancelRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!request) return
    // Focus Cancel, not the destructive action, so Enter can't remove someone by accident
    cancelRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [request, onClose])

  if (!request) return null

  return (
    <div className="dm-overlay confirm-overlay" onClick={onClose}>
      <div
        className="confirm-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-message"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="confirm-dialog-title">{request.title}</h3>
        <p id="confirm-dialog-message">{request.message}</p>
        <div className="confirm-actions">
          <button ref={cancelRef} className="confirm-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            className="confirm-danger"
            onClick={() => {
              request.onConfirm()
              onClose()
            }}
          >
            {request.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
