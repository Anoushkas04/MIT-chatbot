// MITra Community Guidelines: the one source for the /guidelines page and the short
// reminders linked from Community and Network. The enforcement numbers in "consequences"
// mirror backend/app/moderation_engine.py (strikes) and backend/app/safety.py (reports,
// suspension lengths); update both together.

export const GUIDELINES_VERSION = '2026-11'
export const GUIDELINES_UPDATED = 'November 2026'

export type GuidelineSection = { id: string; title: string; intro?: string; points: string[] }

export const guidelineSections: GuidelineSection[] = [
  {
    id: 'respect',
    title: 'Be respectful',
    intro: 'This covers questions, answers, replies, your profile and private messages.',
    points: [
      'No harassment, bullying, threats or targeting a student, faculty member or staff member.',
      'No hate speech, including casteist, racist, religious, gender-based or regional abuse.',
      'Disagree with ideas, not people. Keep criticism of courses or offices about the issue.',
    ],
  },
  {
    id: 'safe',
    title: 'Keep it safe and legal',
    points: [
      'No sexual or explicit content.',
      'No buying, selling or arranging drugs or other illegal substances.',
      'No forged documents (hall tickets, certificates, medical notes) and no hacking university systems or accounts.',
      'Discussing these topics for coursework or research is fine, as long as nothing is being offered or arranged.',
    ],
  },
  {
    id: 'integrity',
    title: 'Academic integrity',
    points: [
      'No sharing or asking for leaked question papers, or answers during an exam or test.',
      'No offers to write assignments, take tests or do lab records for someone else.',
      'Previous-year papers, notes and study tips that are meant to be shared are welcome.',
    ],
  },
  {
    id: 'accuracy',
    title: 'Be accurate and helpful',
    intro: 'Posts the MITra team verifies become part of what the chatbot answers from, so accuracy matters.',
    points: [
      'Answer from what you know or have experienced, and say so when you are unsure.',
      'Mention when information might be outdated, such as timings, fees or procedures that change each year.',
      'Point to the official source (notice, regulation, calendar) when there is one.',
      'Keep posts on topic: campus, academics, clubs, hostel and student life.',
    ],
  },
  {
    id: 'privacy',
    title: 'Respect privacy',
    points: [
      "Don't post anyone's learner ID, registration number, phone number, address or photos without their consent.",
      "Don't share screenshots of private chats or unannounced marks or grade sheets.",
      'Private chats are only possible between accepted connections. Treat them as private.',
      'When you report someone, your messages are never included, and the person is not told who reported them.',
    ],
  },
  {
    id: 'spam',
    title: 'No spam, ads or impersonation',
    points: [
      'No advertising, paid promotion, referral links or repeated posts.',
      'No pretending to be someone else, including faculty, a club, an office or the MITra team.',
      'Club and event announcements are fine when they are relevant and posted once.',
    ],
  },
  {
    id: 'wellbeing',
    title: 'If you or someone else is not safe',
    points: [
      'If someone may harm themselves or others, report them with "Self-harm concern" so the MITra team can follow up.',
      'In an emergency, call 112 (India emergency number).',
      'For mental health support, call Tele-MANAS on 14416, free and available 24/7, or talk to your faculty advisor.',
    ],
  },
  {
    id: 'reporting',
    title: 'Reporting and blocking',
    points: [
      'Report a student from the menu in your chat with them in Network. Choose a reason and add details if you want.',
      'Blocking stops messages both ways and hides you from each other in search.',
      'Community posts are checked automatically before they are published, and the MITra team removes posts that break these guidelines.',
    ],
  },
  {
    id: 'consequences',
    title: 'What happens if the guidelines are broken',
    points: [
      'A post that breaks the guidelines is blocked before it is published, and your account gets a strike.',
      'On the 5th strike, your account is suspended for 7 days.',
      'If 10 different students report an account, it is suspended until the MITra team reviews it.',
      'The MITra team may also remove posts, send a warning, or suspend an account for 1, 3, 7 or 30 days, or until further review.',
      'While suspended you can still sign in, see the reason, and send a plea from the banner at the top of the app.',
      'If your account was disabled, you can appeal from the sign-in page.',
    ],
  },
]
