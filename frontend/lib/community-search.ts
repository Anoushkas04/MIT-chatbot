import type { CommunityComment, CommunityQuestion } from '@/lib/mock-data'

/**
 * Lightweight in-browser "semantic" search for the Community page. There is no
 * embedding model on the client, so each interest tag carries a vocabulary of
 * related campus terms: a query is mapped onto those topics and posts in a
 * matched topic rank even when they don't share the query's exact words.
 */
export const TOPIC_VOCAB: Record<string, string[]> = {
  Academics: [
    'academic', 'course', 'subject', 'class', 'lecture', 'professor', 'prof', 'faculty', 'teacher', 'credit',
    'cgpa', 'gpa', 'sgpa', 'grade', 'syllabus', 'elective', 'assignment', 'lab', 'study', 'notes', 'semester',
    'sem', 'department', 'hod', 'tutorial', 'project', 'minor', 'major', 'branch', 'office hours',
  ],
  Attendance: [
    'attendance', 'attend', 'absent', 'present', 'bunk', 'proxy', '75', 'percent', 'shortage', 'condonation',
    'detained', 'debarred', 'medical leave', 'leave', 'od', 'duty leave',
  ],
  Exams: [
    'exam', 'midsem', 'endsem', 'mid sem', 'end sem', 'test', 'quiz', 'paper', 'revision', 'revise', 'prep',
    'prepare', 'preparation', 'marks', 'result', 'makeup', 'supplementary', 'reval', 'revaluation', 'pyq',
    'question paper', 'sessional', 'study group', 'numerical', 'syllabus',
  ],
  Hostel: [
    'hostel', 'room', 'roommate', 'block', 'warden', 'mess', 'food', 'laundry', 'wifi', 'curfew',
    'accommodation', 'pg', 'stay', 'dorm', 'fc', 'canteen',
  ],
  'Campus Life': [
    'campus', 'life', 'fest', 'revels', 'techtatva', 'cafe', 'canteen', 'sports', 'gym', 'marena', 'friends',
    'weekend', 'transport', 'auto', 'bus', 'beach', 'event', 'social', 'food',
  ],
  Clubs: [
    'club', 'society', 'team', 'chapter', 'ieee', 'acm', 'formula manipal', 'recruitment', 'induction', 'member',
    'join', 'student project', 'hackathon', 'committee', 'board',
  ],
  Opportunities: [
    'internship', 'intern', 'placement', 'job', 'research', 'competition', 'hackathon', 'scholarship', 'grant',
    'funding', 'fund', 'stipend', 'career', 'resume', 'cv', 'interview', 'startup', 'reimbursement', 'travel grant',
  ],
  Registration: [
    'registration', 'register', 'enroll', 'enrollment', 'slcm', 'portal', 'add drop', 'elective selection',
    'fee', 'fees', 'deadline', 'course registration', 'credit', 'minor',
  ],
}

const STOPWORDS = new Set([
  'a', 'an', 'the', 'is', 'are', 'was', 'be', 'to', 'of', 'in', 'on', 'for', 'and', 'or', 'how', 'what', 'when',
  'where', 'who', 'why', 'do', 'does', 'i', 'my', 'me', 'it', 'any', 'can', 'with', 'about', 'should', 'there',
])

// Crude suffix stripping so "exams"/"exam" and "preparing"/"prepare" line up.
function stem(word: string): string {
  if (word.length > 5 && word.endsWith('ing')) return word.slice(0, -3)
  if (word.length > 4 && word.endsWith('ed')) return word.slice(0, -2)
  if (word.length > 3 && word.endsWith('s') && !word.endsWith('ss')) return word.slice(0, -1)
  return word
}

function normalizeText(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
}

function tokens(text: string): string[] {
  return normalizeText(text)
    .split(' ')
    .filter((w) => w.length > 1 && !STOPWORDS.has(w))
    .map(stem)
}

function termMatches(term: string, text: string, tokenSet: Set<string>): boolean {
  const norm = normalizeText(term)
  return norm.includes(' ') ? ` ${text} `.includes(` ${norm} `) : tokenSet.has(stem(norm))
}

/** Interest tags the query relates to, strongest first. */
export function matchTopics(query: string): string[] {
  const text = normalizeText(query)
  const tokenList = tokens(query)
  const tokenSet = new Set(tokenList)
  const hits: { topic: string; score: number }[] = []
  for (const [topic, vocab] of Object.entries(TOPIC_VOCAB)) {
    let score = termMatches(topic, text, tokenSet) ? 2 : 0
    for (const term of vocab) if (termMatches(term, text, tokenSet)) score += 1
    // Partial words while typing ("regis" -> registration).
    if (score === 0 && tokenList.some((t) => t.length >= 4 && [topic, ...vocab].some((v) => normalizeText(v).startsWith(t)))) {
      score = 0.5
    }
    if (score > 0) hits.push({ topic, score })
  }
  return hits.sort((a, b) => b.score - a.score).map((h) => h.topic)
}

function threadText(comments: CommunityComment[]): string {
  return comments.map((c) => `${c.body} ${threadText(c.replies ?? [])}`).join(' ')
}

// Scores below this come from a single incidental related word, which reads as noise.
export const MIN_RELEVANCE = 2

/** Relevance of a question to the query; below MIN_RELEVANCE it should be hidden. */
export function scoreQuestion(question: CommunityQuestion, query: string, topics: string[]): number {
  const queryTokens = [...new Set(tokens(query))]
  if (queryTokens.length === 0) return 0
  const title = new Set(tokens(question.title))
  const body = new Set(tokens(question.body))
  const answersText = threadText(question.answers)
  const answers = new Set(tokens(answersText))
  const allText = normalizeText(`${question.title} ${question.body} ${answersText}`)
  const allTokens = new Set([...title, ...body, ...answers])

  let score = 0
  for (const t of queryTokens) {
    if (title.has(t)) score += 3
    else if (body.has(t)) score += 2
    else if (answers.has(t)) score += 1
  }
  topics.forEach((topic, i) => {
    const weight = i === 0 ? 1 : 0.6
    if (question.tags.includes(topic)) score += 4 * weight
    const related = TOPIC_VOCAB[topic].filter((term) => termMatches(term, allText, allTokens)).length
    score += Math.min(related, 3) * weight
  })
  return score
}
