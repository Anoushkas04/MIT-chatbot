import { redirect } from 'next/navigation'

// The admin console starts at Monitoring; /admin stays valid for old links and bookmarks.
export default function AdminIndex() {
  redirect('/admin/monitoring')
}
