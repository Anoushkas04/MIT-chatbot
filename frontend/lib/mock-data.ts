import {
  Briefcase,
  Building2,
  CalendarDays,
  FileText,
  Flame,
  GraduationCap,
  HelpCircle,
  Lightbulb,
  MapPin,
  Sparkles,
  Trophy,
  Users,
  type LucideIcon,
} from 'lucide-react'

// All data in this file is clearly-fictional placeholder/demo content, not
// real MIT Manipal records. It seeds local mock state (see use-local-state.ts)
// until a real backend exists to replace it.

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

export type DiscoveryCategory = 'club' | 'project' | 'event' | 'opportunity'

export type DiscoveryItem = {
  id: string
  title: string
  type: string
  category: DiscoveryCategory
  meta: string
  tone: 'coral' | 'blue' | 'yellow' | 'green'
  icon: LucideIcon
  why: string
}

export const discoveries: DiscoveryItem[] = [
  { id: 'd1', title: 'Manipal Hackathon 2026', type: 'Competition', category: 'event', meta: 'Oct 25 · Innovation Centre', tone: 'coral', icon: Flame, why: 'Matches your interest in building' },
  { id: 'd2', title: 'IEEE Student Branch', type: 'Club', category: 'club', meta: '48 active members · Technical', tone: 'blue', icon: Lightbulb, why: 'Popular with CSE students' },
  { id: 'd3', title: 'Design Thinking Workshop', type: 'Workshop', category: 'event', meta: 'Nov 02 · Student Plaza', tone: 'yellow', icon: Sparkles, why: 'Based on your saved events' },
  { id: 'd4', title: 'Product Lab · Student Innovation Cell', type: 'Project', category: 'project', meta: 'Rolling applications · 6 spots open', tone: 'green', icon: Users, why: 'A new way to explore your interests' },
  { id: 'd5', title: 'Robotics Club', type: 'Club', category: 'club', meta: '32 active members · Technical', tone: 'blue', icon: Lightbulb, why: 'Matches your interest in robotics' },
  { id: 'd6', title: 'Summer Research Internship — AI Lab', type: 'Internship', category: 'opportunity', meta: 'Apply by Dec 10 · 4 openings', tone: 'coral', icon: Briefcase, why: 'Fits your AI interest' },
  { id: 'd7', title: 'Campus Photography Walk', type: 'Event', category: 'event', meta: 'Nov 08 · Lake Side', tone: 'yellow', icon: CalendarDays, why: 'Based on your saved events' },
  { id: 'd8', title: 'Case Study Competition — Finance Club', type: 'Competition', category: 'opportunity', meta: 'Teams of 3 · Reg closes Nov 15', tone: 'green', icon: Trophy, why: 'Popular with 5th semester students' },
]

export type SearchResult = {
  id: string
  title: string
  kind: string
  excerpt: string
  icon: LucideIcon
}

export const searchResults: SearchResult[] = [
  { id: 's1', title: 'Academic Regulations 2025–26', kind: 'Official document', excerpt: 'Rules governing attendance, examinations, grading and academic progression.', icon: FileText },
  { id: 's2', title: 'How do I apply for a bonafide certificate?', kind: 'Campus procedure', excerpt: 'A step-by-step guide from the Student Affairs office, updated Aug 2026.', icon: HelpCircle },
  { id: 's3', title: 'End semester examination schedule', kind: 'Notice · Examination Cell', excerpt: 'B.Tech III & V semester end semester examinations begin December 01.', icon: CalendarDays },
  { id: 's4', title: 'Minimum attendance requirement', kind: 'Academic regulation', excerpt: 'Students must maintain at least 75% attendance in each course to be eligible to appear for exams.', icon: GraduationCap },
  { id: 's5', title: 'Course registration deadlines', kind: 'Notice · Academic Cell', excerpt: 'Elective and credit registration for the even semester closes November 01.', icon: CalendarDays },
  { id: 's6', title: 'Hostel leave and outpass policy', kind: 'Campus procedure', excerpt: 'How to request an overnight outpass or vacation leave from your hostel warden.', icon: Building2 },
]

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

export type AttendanceCourse = { id: string; course: string; held: number; attended: number }

export const defaultAttendanceCourses: AttendanceCourse[] = [
  { id: 'a1', course: 'Data Structures', held: 42, attended: 38 },
  { id: 'a2', course: 'Operating Systems', held: 40, attended: 30 },
  { id: 'a3', course: 'Computer Networks', held: 39, attended: 33 },
]

export type Professor = { id: string; name: string; dept: string; cabin: string; email: string }

export const professors: Professor[] = [
  { id: 'p1', name: 'Dr. Meera Kulkarni', dept: 'Computer Science & Engineering', cabin: 'AB4 · 2nd floor · 214', email: 'meera.kulkarni@manipal.edu' },
  { id: 'p2', name: 'Dr. Rohan Saldanha', dept: 'Computer Science & Engineering', cabin: 'AB4 · 2nd floor · 221', email: 'rohan.saldanha@manipal.edu' },
  { id: 'p3', name: 'Dr. Priya Nair', dept: 'Electronics & Communication', cabin: 'AB3 · 1st floor · 108', email: 'priya.nair@manipal.edu' },
  { id: 'p4', name: 'Dr. Ashwin Rao', dept: 'Mechanical Engineering', cabin: 'AB2 · Ground floor · 05', email: 'ashwin.rao@manipal.edu' },
  { id: 'p5', name: 'Dr. Leela Bhat', dept: 'Mathematics', cabin: 'AB1 · 3rd floor · 310', email: 'leela.bhat@manipal.edu' },
]

export type Lab = { id: string; name: string; building: string; floor: string; room: string; serves: string }

export const labs: Lab[] = [
  { id: 'l1', name: 'AI & Data Science Lab', building: 'AB4', floor: '3rd floor', room: '305', serves: 'CSE, AIML' },
  { id: 'l2', name: 'Networks Lab', building: 'AB4', floor: '2nd floor', room: '208', serves: 'CSE, ECE' },
  { id: 'l3', name: 'Robotics Lab', building: 'AB2', floor: 'Ground floor', room: '02', serves: 'Mechatronics, ECE' },
  { id: 'l4', name: 'VLSI Design Lab', building: 'AB3', floor: '1st floor', room: '112', serves: 'ECE' },
  { id: 'l5', name: 'Thermal Sciences Lab', building: 'AB2', floor: '1st floor', room: '14', serves: 'Mechanical' },
]

export type Document = { id: string; title: string; category: string; updated: string }

export const documents: Document[] = [
  { id: 'doc1', title: 'Academic Regulations 2025–26', category: 'Regulation', updated: 'Aug 2026' },
  { id: 'doc2', title: 'B.Tech Syllabus — CSE', category: 'Syllabus', updated: 'Jul 2026' },
  { id: 'doc3', title: 'Bonafide certificate request form', category: 'Form', updated: 'Jun 2026' },
  { id: 'doc4', title: 'Hostel outpass request form', category: 'Form', updated: 'May 2026' },
  { id: 'doc5', title: 'End semester exam timetable', category: 'Notice', updated: 'Oct 2026' },
  { id: 'doc6', title: 'Scholarship application guidelines', category: 'Guideline', updated: 'Sep 2026' },
]

export type HelpdeskContact = { id: string; role: string; office: string; timings: string }

export const helpdeskContacts: HelpdeskContact[] = [
  { id: 'h1', role: 'Academic Cell', office: 'Admin Block · Room 12', timings: 'Mon–Fri, 9:30–4:30' },
  { id: 'h2', role: 'Examination Cell', office: 'Admin Block · Room 18', timings: 'Mon–Fri, 10:00–4:00' },
  { id: 'h3', role: 'Student Affairs Office', office: 'Admin Block · Room 05', timings: 'Mon–Sat, 9:00–5:00' },
  { id: 'h4', role: 'Scholarship Cell', office: 'Admin Block · Room 21', timings: 'Tue & Thu, 11:00–2:00' },
  { id: 'h5', role: 'International Relations Office', office: 'Admin Block · Room 30', timings: 'Mon–Fri, 9:30–4:30' },
]

export type CouncilMember = { id: string; name: string; position: string; branch: string }

export const councilMembers: CouncilMember[] = [
  { id: 'c1', name: 'Sanya Mehta', position: 'General Secretary', branch: 'CSE, 7th semester' },
  { id: 'c2', name: 'Varun Kapoor', position: 'Cultural Secretary', branch: 'ECE, 5th semester' },
  { id: 'c3', name: 'Diya Shetty', position: 'Technical Secretary', branch: 'CSE, 7th semester' },
  { id: 'c4', name: 'Rahul Menon', position: 'Sports Secretary', branch: 'Mechanical, 5th semester' },
]

export type Amenity = { id: string; name: string; category: string; location: string }

export const amenities: Amenity[] = [
  { id: 'am1', name: 'Food Court', category: 'Food', location: 'Student Plaza' },
  { id: 'am2', name: 'Health Centre', category: 'Medical', location: 'Near AB1' },
  { id: 'am3', name: 'Sports Complex', category: 'Sports', location: 'Behind AB2' },
  { id: 'am4', name: 'Central Library', category: 'Academic', location: 'Library Block' },
  { id: 'am5', name: 'ATM & Bank', category: 'Services', location: 'Near Main Gate' },
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

export const defaultNetworkPeople: NetworkPerson[] = [
  { id: 'n1', name: 'Tanvi Rao', initials: 'TR', branch: 'CSE', semester: '5th sem', sharedInterests: ['Artificial Intelligence', 'Research'], status: 'suggested' },
  { id: 'n2', name: 'Karan Bhatt', initials: 'KB', branch: 'ECE', semester: '5th sem', sharedInterests: ['Robotics'], status: 'suggested' },
  { id: 'n3', name: 'Nisha Pillai', initials: 'NP', branch: 'CSE', semester: '3rd sem', sharedInterests: ['Design', 'Web Development'], status: 'connected' },
  { id: 'n4', name: 'Arjun Verma', initials: 'AV', branch: 'Mechanical', semester: '7th sem', sharedInterests: ['Entrepreneurship'], status: 'suggested' },
  { id: 'n5', name: 'Fatima Sheikh', initials: 'FS', branch: 'CSE', semester: '5th sem', sharedInterests: ['Artificial Intelligence', 'Competitive Programming'], status: 'connected' },
  { id: 'n6', name: 'Rohit Dsouza', initials: 'RD', branch: 'ECE', semester: '5th sem', sharedInterests: ['Design'], status: 'suggested' },
  { id: 'n7', name: 'Ananya Iyer', initials: 'AI', branch: 'CSE', semester: '5th sem', sharedInterests: ['Research', 'Public Speaking'], status: 'suggested' },
  { id: 'n8', name: 'Sameer Khan', initials: 'SK', branch: 'CSE', semester: '5th sem', sharedInterests: ['Robotics', 'Artificial Intelligence'], status: 'pending' },
  { id: 'n9', name: 'Priyanka Das', initials: 'PD', branch: 'CSE', semester: '5th sem', sharedInterests: ['Competitive Programming'], status: 'incoming' },
  { id: 'n10', name: 'Yusuf Ali', initials: 'YA', branch: 'ECE', semester: '5th sem', sharedInterests: ['Music'], status: 'incoming' },
]

export type DirectMessage = { id: string; from: 'me' | 'them'; text: string; time: string }

export const defaultMessages: Record<string, DirectMessage[]> = {
  n3: [
    { id: 'm1', from: 'them', text: 'Hey! Saw you\'re also into web dev, are you joining the design jam next week?', time: '10:12 AM' },
    { id: 'm2', from: 'me', text: 'Yeah planning to! Are you on a team yet?', time: '10:15 AM' },
    { id: 'm3', from: 'them', text: 'Not yet, want to team up?', time: '10:16 AM' },
  ],
  n5: [
    { id: 'm1', from: 'them', text: 'That CP contest this weekend, you in?', time: 'Yesterday' },
    { id: 'm2', from: 'me', text: 'Definitely, let\'s do a virtual contest together before that too', time: 'Yesterday' },
  ],
}

// ---- Planner ----

export type PlannerTask = {
  id: string
  date: string // YYYY-MM-DD
  title: string
  category: string
  done: boolean
}

function isoDaysFromToday(offset: number) {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  return d.toISOString().slice(0, 10)
}

export const defaultPlannerTasks: PlannerTask[] = [
  { id: 't1', date: isoDaysFromToday(2), title: 'Submit OS assignment', category: 'Academic', done: false },
  { id: 't2', date: isoDaysFromToday(5), title: 'Manipal Hackathon 2026', category: 'Event', done: false },
  { id: 't3', date: isoDaysFromToday(10), title: 'Course registration closes', category: 'Important', done: false },
  { id: 't4', date: isoDaysFromToday(-1), title: 'Data Structures quiz', category: 'Academic', done: true },
]
