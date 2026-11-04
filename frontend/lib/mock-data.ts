// Shared types and empty defaults for local state (see use-local-state.ts). The community
// threads and the signed-out profile below are placeholders; campus data (clubs, events,
// faculty, calendar) lives in its own source-backed modules.

export const interestOptions = [
  'Artificial Intelligence',
  'Web Development',
  'Robotics',
  'Design',
  'Competitive Programming',
  'Entrepreneurship',
  'Music',
  'Photography',
  'Public Speaking',
  'Sports',
  'Finance',
  'Research',
] as const

export type ProfileAvatar = { emoji: string; color: string }

export const avatarChoices: ProfileAvatar[] = [
  { emoji: '🦊', color: '#f5ded6' },
  { emoji: '🐼', color: '#dbe9e7' },
  { emoji: '🦁', color: '#f4ecc9' },
  { emoji: '🐧', color: '#dce9d5' },
  { emoji: '🐸', color: '#d8ef68' },
  { emoji: '🦉', color: '#e8eeea' },
  { emoji: '🐢', color: '#c8dfdb' },
  { emoji: '🦄', color: '#efd2c8' },
]

export type Profile = {
  name: string
  initials: string
  learnerId: string
  regNumber: string
  branch: string
  semester: string
  avatar: ProfileAvatar
  interests: string[]
}

export const defaultProfile: Profile = {
  name: 'Arjun Rasoju',
  initials: 'AS',
  learnerId: 'rasoju.mitmpl2023@learner.manipal.edu',
  regNumber: '220905123',
  branch: 'Computer Science & Engineering',
  semester: '5th semester',
  avatar: avatarChoices[0],
  interests: ['Artificial Intelligence', 'Robotics', 'Design'],
}

// MIT Manipal 10-point grade scale (Regulations 4.8.1), as offered by the GPA calculator.
export const gradeOptions: { grade: string; value: number }[] = [
  { grade: 'A+', value: 10 },
  { grade: 'A', value: 9 },
  { grade: 'B', value: 8 },
  { grade: 'C', value: 7 },
  { grade: 'D', value: 6 },
  { grade: 'E', value: 5 },
  { grade: 'F', value: 0 },
]

// ---- Community (Reddit/YouTube-style Q&A) ----

// Answers and replies share one recursive shape so threads can nest indefinitely.
export type CommunityComment = {
  id: string
  author: string
  initials: string
  time: string
  body: string
  votes: number
  replies: CommunityComment[]
  edited?: boolean
  deleted?: boolean
  // Set by the backend: posted by an admin ("MITra Official"), and whether it's the viewer's own.
  isOfficial?: boolean
  isMine?: boolean
}

export type CommunityAnswer = CommunityComment
export type CommunityReply = CommunityComment

export type CommunityQuestion = {
  id: string
  title: string
  body: string
  tags: string[]
  author: string
  initials: string
  time: string
  votes: number
  answers: CommunityAnswer[]
  edited?: boolean
  verified?: boolean
  isOfficial?: boolean
  isMine?: boolean
}

export const communityQuestions: CommunityQuestion[] = [
  {
    id: 'q1',
    title: 'What exactly counts towards the 75% attendance rule?',
    body: 'Does attendance in labs count separately from theory classes, or is it all pooled into one percentage per course?',
    tags: ['Academics', 'Attendance'],
    author: 'Kavya R.',
    initials: 'KR',
    time: '2d ago',
    votes: 14,
    answers: [
      { id: 'q1a1', author: 'Sanya Mehta', initials: 'SM', time: '2d ago', body: 'Labs and theory are tracked separately per course code — check the per-course breakup on the portal, not just the overall number.', votes: 19, replies: [
        { id: 'q1a1r1', author: 'Kavya R.', initials: 'KR', time: '1d ago', body: 'That explains it, thank you!', votes: 2, replies: [] },
      ] },
      { id: 'q1a2', author: 'Rahul Menon', initials: 'RM', time: '1d ago', body: 'Also worth noting condonation forms exist if you drop just below 75% for medical reasons.', votes: 6, replies: [] },
    ],
  },
  {
    id: 'q2',
    title: 'Best way to prepare for the OS end-sem besides PYQs?',
    body: 'Finished the previous year questions twice already, looking for anything else that actually helped people.',
    tags: ['Academics', 'Exams'],
    author: 'Devansh P.',
    initials: 'DP',
    time: '4d ago',
    votes: 22,
    answers: [
      { id: 'q2a1', author: 'Diya Shetty', initials: 'DS', time: '3d ago', body: 'Gate Smashers playlist on OS plus re-deriving the scheduling numericals by hand helped me more than re-reading notes.', votes: 15, replies: [] },
      { id: 'q2a2', author: 'Varun Kapoor', initials: 'VK', time: '3d ago', body: 'Form a study group and explain deadlock avoidance to each other out loud, it exposes gaps fast.', votes: 11, replies: [
        { id: 'q2a2r1', author: 'Devansh P.', initials: 'DP', time: '2d ago', body: 'Doing this tonight, thanks!', votes: 1, replies: [] },
      ] },
      { id: 'q2a3', author: 'Kavya R.', initials: 'KR', time: '2d ago', body: 'Professor Saldanha\'s office hours on Thursdays are criminally underused, go ask there.', votes: 4, replies: [] },
    ],
  },
  {
    id: 'q3',
    title: 'Anyone know how hostel outpass approval timing actually works?',
    body: 'Submitted an outpass request two days ago and it still shows pending. Is there a usual turnaround time?',
    tags: ['Hostel', 'Campus Life'],
    author: 'Ishaan T.',
    initials: 'IT',
    time: '6h ago',
    votes: 3,
    answers: [],
  },
  {
    id: 'q4',
    title: 'Is it worth joining both IEEE and Robotics Club or should I pick one?',
    body: 'Both are doing interesting projects this semester and I can\'t decide, curious what people who\'ve done both think.',
    tags: ['Clubs'],
    author: 'Meera Joshi',
    initials: 'MJ',
    time: '1d ago',
    votes: 9,
    answers: [
      { id: 'q4a1', author: 'Sanya Mehta', initials: 'SM', time: '20h ago', body: 'Depends on your semester load — I did both in 3rd sem and it was tight but doable if the projects don\'t overlap in deadlines.', votes: 8, replies: [] },
    ],
  },
  {
    id: 'q5',
    title: 'Elective registration closed before I could pick — now what?',
    body: 'Missed the window for elective registration by a day. Is there a late-add process or do I just get auto-assigned?',
    tags: ['Academics', 'Registration'],
    author: 'Rhea D souza',
    initials: 'RD',
    time: '3d ago',
    votes: 7,
    answers: [],
  },
  {
    id: 'q6',
    title: 'How do people usually fund side projects / hackathon travel?',
    body: 'Our team qualified for an offline hackathon round and travel + stay isn\'t cheap. Does the college sponsor anything for this?',
    tags: ['Opportunities', 'Clubs'],
    author: 'Aarav Singh',
    initials: 'AS',
    time: '5d ago',
    votes: 18,
    answers: [
      { id: 'q6a1', author: 'Diya Shetty', initials: 'DS', time: '4d ago', body: 'Student Innovation Cell has a travel grant form, worth 60–70% reimbursement if you place or even just qualify for finals.', votes: 21, replies: [
        { id: 'q6a1r1', author: 'Aarav Singh', initials: 'AS', time: '4d ago', body: 'This is huge, didn\'t know this existed.', votes: 3, replies: [] },
      ] },
      { id: 'q6a2', author: 'Rahul Menon', initials: 'RM', time: '3d ago', body: 'Your department also sometimes has a small discretionary fund, ask your HOD\'s office directly.', votes: 5, replies: [] },
    ],
  },
]

// ---- Network (LinkedIn-style connections) ----

export type NetworkStatus = 'suggested' | 'pending' | 'incoming' | 'connected' | 'dismissed' | 'blocked'

export type NetworkPerson = {
  id: string
  name: string
  initials: string
  branch: string
  semester: string
  sharedInterests: string[]
  status: NetworkStatus
  // Set for people found through account search; their backend user id, used for reports.
  accountId?: string
}

// Network only shows registered students from the backend (see use-network.ts).
export const defaultNetworkPeople: NetworkPerson[] = []

// A thing someone else did that concerns you. `at` is a timestamp for live events;
// seeded demo events carry a display `time` instead.
export type ActivityEvent = { id: string; kind: 'accepted'; personId: string; at?: number; time?: string }

export const defaultActivity: ActivityEvent[] = []

export type DirectMessage = { id: string; from: 'me' | 'them'; text: string; time: string }

export const defaultMessages: Record<string, DirectMessage[]> = {}

// ---- Planner ----

export type PlannerTask = {
  id: string
  date: string // YYYY-MM-DD
  title: string
  category: string
  done: boolean
}

// Personal tasks only; official dates come from academic-calendar.ts and are shown separately.
export const defaultPlannerTasks: PlannerTask[] = []

// Sample tasks earlier versions seeded into every planner. Dropped on load so only the student's own remain.
const SAMPLE_TASKS: Record<string, string> = {
  t1: 'Submit OS assignment',
  t2: 'Manipal Hackathon 2026',
  t3: 'Course registration closes',
  t4: 'Data Structures quiz',
}

export function withoutSampleTasks(tasks: PlannerTask[]) {
  return tasks.filter((t) => SAMPLE_TASKS[t.id] !== t.title)
}
